pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

ApplicationWindow {
	id: window
	width: 1440
	height: 900
	minimumWidth: 900
	minimumHeight: 560
	visible: true
	title: (notes.dirty ? "• " : "") + (notes.currentTitle || "School Notes")
		+ (notes.currentTitle ? " — School Notes" : "")
	color: theme.background

	// Design tokens (same as VL): keep colours here, not scattered around.
	QtObject {
		id: theme
		readonly property color background: "#17191d"
		readonly property color panel: "#202329"
		readonly property color panelRaised: "#282c33"
		readonly property color border: "#383d46"
		readonly property color text: "#e3e7ed"
		readonly property color muted: "#929ba8"
		readonly property color accent: "#72a7ff"
		readonly property color ok: "#6fcf97"
		readonly property color warn: "#e5b567"
		readonly property color error: "#f28b82"
	}

	palette.window: theme.panel
	palette.windowText: theme.text
	palette.base: theme.panelRaised
	palette.text: theme.text
	palette.button: theme.panelRaised
	palette.buttonText: theme.text
	palette.highlight: theme.accent
	palette.highlightedText: "#101722"
	palette.mid: theme.border
	palette.light: "#343943"
	palette.dark: "#15171b"
	palette.placeholderText: theme.muted

	readonly property bool hasLesson: notes.currentPath !== ""

	// -- Shortcuts -----------------------------------------------------------

	Shortcut {
		sequence: "Ctrl+S"
		context: Qt.ApplicationShortcut
		onActivated: if (notes.save() && window.hasLesson) toast.show("Saved")
	}
	Shortcut {
		sequences: ["Ctrl+Return", "Ctrl+Enter"]
		context: Qt.ApplicationShortcut
		onActivated: notes.format()
	}
	Shortcut {
		sequence: "Ctrl+R"
		context: Qt.ApplicationShortcut
		onActivated: notes.rerender()
	}
	Shortcut {
		sequence: "Ctrl+N"
		context: Qt.ApplicationShortcut
		onActivated: { notes.newLesson(); editor.forceActiveFocus() }
	}
	Shortcut {
		sequence: "Ctrl+Shift+N"
		context: Qt.ApplicationShortcut
		onActivated: subjectPopup.open()
	}

	onClosing: notes.save()

	// -- Header --------------------------------------------------------------

	header: Rectangle {
		height: 44
		color: theme.panel
		Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: theme.border }

		RowLayout {
			anchors.fill: parent
			anchors.leftMargin: 14
			anchors.rightMargin: 10
			spacing: 10

			Text {
				text: "School Notes"
				color: theme.muted
				font.pixelSize: 13
				font.bold: true
			}
			Text {
				text: notes.currentSubject ? "/  " + notes.currentSubject : ""
				color: theme.muted
				font.pixelSize: 13
			}
			Text {
				Layout.fillWidth: true
				text: notes.currentTitle
				color: theme.text
				font.pixelSize: 13
				elide: Text.ElideRight
			}
			Spinner {
				visible: notes.busy
				Layout.preferredWidth: 16
				Layout.preferredHeight: 16
			}
			VButton {
				objectName: "rerenderButton"
				text: "Re-render  Ctrl+R"
				subtle: true
				enabled: window.hasLesson && !notes.busy
				onClicked: notes.rerender()
			}
			VButton {
				objectName: "formatButton"
				text: notes.busy ? "Working…" : "Format  Ctrl+↵"
				kind: "primary"
				enabled: window.hasLesson && !notes.busy
				onClicked: notes.format()
			}
		}
	}

	// -- Body ----------------------------------------------------------------

	SplitView {
		anchors.fill: parent
		orientation: Qt.Horizontal

		handle: Rectangle {
			implicitWidth: 1
			color: SplitHandle.hovered || SplitHandle.pressed ? theme.accent : theme.border
		}

		// Sidebar: subjects and lessons
		Rectangle {
			SplitView.preferredWidth: 230
			SplitView.minimumWidth: 170
			color: theme.panel

			ColumnLayout {
				anchors.fill: parent
				spacing: 0

				SectionHeader {
					title: "SUBJECTS"
					onAdd: subjectPopup.open()
					addTip: "New subject (Ctrl+Shift+N)"
				}
				ListView {
					id: subjectList
					objectName: "subjectList"
					Layout.fillWidth: true
					Layout.preferredHeight: Math.min(contentHeight, 220)
					clip: true
					model: notes.subjects
					delegate: SidebarRow {
						required property string modelData
						label: modelData
						selected: modelData === notes.currentSubject
						onClicked: notes.selectSubject(modelData)
					}
				}
				Text {
					visible: notes.subjects.length === 0
					Layout.fillWidth: true
					Layout.margins: 14
					text: "No subjects yet.\nPress Ctrl+Shift+N."
					color: theme.muted
					font.pixelSize: 12
				}

				SectionHeader {
					title: "LESSONS"
					visible: notes.currentSubject !== ""
					onAdd: { notes.newLesson(); editor.forceActiveFocus() }
					addTip: "New lesson (Ctrl+N)"
				}
				ListView {
					id: lessonList
					objectName: "lessonList"
					Layout.fillWidth: true
					Layout.fillHeight: true
					clip: true
					model: notes.lessons
					delegate: SidebarRow {
						required property var modelData
						label: modelData.topic
						detail: modelData.date
						dot: modelData.state === "ok" ? theme.ok
							: modelData.state === "stale" ? theme.warn : theme.border
						dotTip: modelData.state === "ok" ? "PDF up to date"
							: modelData.state === "stale" ? "Text changed since the last format" : "Not formatted yet"
						selected: modelData.path === notes.currentPath
						onClicked: notes.openLesson(modelData.path)
					}
					ScrollBar.vertical: ScrollBar {}
				}

				UsagePanel {
					Layout.fillWidth: true
				}
			}
		}

		// Editor
		Rectangle {
			SplitView.fillWidth: true
			SplitView.minimumWidth: 280
			color: "#1b1d22"

			ScrollView {
				id: editorScroll
				anchors.fill: parent
				visible: window.hasLesson

				TextArea {
					id: editor
					objectName: "editor"
					// Edits are only reported once the real text is loaded;
					// otherwise the empty start value would be saved over it.
					property bool loading: true
					Component.onCompleted: {
						text = notes.text
						loading = false
					}

					wrapMode: TextArea.Wrap
					font.family: monoFont
					font.pixelSize: 14
					color: theme.text
					selectionColor: "#3b6fd4"
					selectedTextColor: "#ffffff"
					placeholderText: "Write your notes here. Messy is fine.\n\n"
						+ "Ctrl+Enter formats them into a PDF.\n"
						+ "Optional tags: <b>bold</b> <i>italic</i> <red>red</red> <sub>2</sub> <sup>2</sup>"
					placeholderTextColor: "#5d6573"
					leftPadding: 22
					rightPadding: 22
					topPadding: 18
					bottomPadding: 18
					selectByMouse: true
					background: null
					onTextChanged: if (!loading) notes.edit(text)
				}
			}

			EmptyState {
				visible: !window.hasLesson
				text: notes.subjects.length === 0
					? "Create a subject to start (Ctrl+Shift+N)."
					: "Create a lesson (Ctrl+N)."
			}
		}

		// PDF preview
		PdfPane {
			SplitView.preferredWidth: 620
			SplitView.minimumWidth: 300
		}
	}

	// -- Footer ---------------------------------------------------------------

	footer: Rectangle {
		height: 26
		color: theme.panel
		Rectangle { width: parent.width; height: 1; color: theme.border }

		RowLayout {
			anchors.fill: parent
			anchors.leftMargin: 12
			anchors.rightMargin: 12
			spacing: 12

			Text {
				objectName: "statusText"
				Layout.fillWidth: true
				text: notes.status
				elide: Text.ElideRight
				font.pixelSize: 11
				color: notes.statusKind === "error" ? theme.error
					: notes.statusKind === "ok" ? theme.ok
					: notes.statusKind === "busy" ? theme.accent : theme.muted
			}
			Text {
				text: notes.dirty ? "Unsaved" : (window.hasLesson ? "Saved" : "")
				font.pixelSize: 11
				color: theme.muted
			}
			Text {
				text: notes.notesDir
				font.pixelSize: 11
				color: "#687280"
			}
		}
	}

	Connections {
		target: notes
		function onTextLoaded(text) {
			editor.loading = true
			editor.text = text
			editor.cursorPosition = text.length
			editor.loading = false
		}
	}

	NamePopup {
		id: subjectPopup
		title: "New subject"
		placeholder: "e.g. Fyzika"
		onAccepted: function(name) {
			if (notes.newSubject(name))
				subjectPopup.close()
		}
	}

	Toast {
		id: toast
		anchors.horizontalCenter: parent.horizontalCenter
		anchors.bottom: parent.bottom
		anchors.bottomMargin: 16
	}

	Component.onCompleted: {
		// Fill the editor with whatever lesson the backend opened at start.
		if (window.hasLesson)
			editor.forceActiveFocus()
	}

	// -- Small components ------------------------------------------------------

	component SectionHeader: Item {
		id: sectionHeader
		property string title
		property string addTip
		signal add()

		Layout.fillWidth: true
		implicitHeight: 34

		Text {
			anchors.left: parent.left
			anchors.leftMargin: 14
			anchors.verticalCenter: parent.verticalCenter
			text: sectionHeader.title
			color: theme.muted
			font.pixelSize: 10
			font.bold: true
			font.letterSpacing: 1.2
		}
		VButton {
			anchors.right: parent.right
			anchors.rightMargin: 6
			anchors.verticalCenter: parent.verticalCenter
			text: "+"
			subtle: true
			implicitWidth: 28
			ToolTip.visible: hovered
			ToolTip.text: sectionHeader.addTip
			onClicked: sectionHeader.add()
		}
	}

	component SidebarRow: Rectangle {
		id: row
		property string label
		property string detail
		property color dot: "transparent"
		property string dotTip
		property bool selected: false
		signal clicked()

		width: ListView.view ? ListView.view.width : 200
		height: detail ? 42 : 30
		color: selected ? "#2c3442" : rowMouse.containsMouse ? "#262a31" : "transparent"

		Rectangle {
			visible: row.selected
			width: 3
			height: parent.height
			color: theme.accent
		}
		Rectangle {
			id: dotItem
			visible: row.dot.a > 0
			anchors.left: parent.left
			anchors.leftMargin: 14
			anchors.verticalCenter: parent.verticalCenter
			width: 7
			height: 7
			radius: 4
			color: row.dot
		}
		Column {
			anchors.left: dotItem.visible ? dotItem.right : parent.left
			anchors.leftMargin: dotItem.visible ? 9 : 14
			anchors.right: parent.right
			anchors.rightMargin: 10
			anchors.verticalCenter: parent.verticalCenter
			spacing: 2

			Text {
				width: parent.width
				text: row.label
				color: row.selected ? theme.text : "#c9ced6"
				font.pixelSize: 13
				elide: Text.ElideRight
			}
			Text {
				visible: row.detail !== ""
				text: row.detail
				color: theme.muted
				font.pixelSize: 10
			}
		}
		MouseArea {
			id: rowMouse
			anchors.fill: parent
			hoverEnabled: true
			onClicked: row.clicked()
		}
		ToolTip.visible: rowMouse.containsMouse && row.dotTip !== ""
		ToolTip.delay: 600
		ToolTip.text: row.dotTip
	}

	component EmptyState: Text {
		anchors.centerIn: parent
		width: parent.width - 60
		horizontalAlignment: Text.AlignHCenter
		wrapMode: Text.WordWrap
		color: theme.muted
		font.pixelSize: 13
	}

	component Spinner: Item {
		id: spinner
		Rectangle {
			anchors.fill: parent
			radius: width / 2
			color: "transparent"
			border.width: 2
			border.color: "#3a404a"
		}
		Rectangle {
			width: 4
			height: 4
			radius: 2
			color: theme.accent
			x: spinner.width / 2 - 2
			y: 0
		}
		RotationAnimator on rotation {
			from: 0
			to: 360
			duration: 900
			loops: Animation.Infinite
			running: spinner.visible
		}
	}
}
