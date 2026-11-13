import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Claude usage: the last format's tokens and how full the plan's 5-hour and
// weekly windows are, as bars with their reset times.
Rectangle {
	id: panel
	objectName: "usagePanel"
	implicitHeight: column.implicitHeight + 24
	color: "#1c1f24"

	readonly property var usage: notes.usage

	Rectangle { width: parent.width; height: 1; color: "#383d46" }

	ColumnLayout {
		id: column
		anchors.left: parent.left
		anchors.right: parent.right
		anchors.top: parent.top
		anchors.margins: 14
		anchors.topMargin: 12
		spacing: 9

		Text {
			text: "CLAUDE USAGE"
			color: "#929ba8"
			font.pixelSize: 10
			font.bold: true
			font.letterSpacing: 1.2
		}

		Text {
			objectName: "usageTokens"
			Layout.fillWidth: true
			text: panel.usage.hasTokens
				? "Last format (" + panel.usage.tokensWhen + "): " + panel.usage.tokens
				: "No format yet"
			color: "#c9ced6"
			font.pixelSize: 11
			elide: Text.ElideRight
		}

		LimitBar {
			objectName: "fiveHourBar"
			label: "5 hours"
			window: panel.usage.fiveHour
		}
		LimitBar {
			objectName: "weekBar"
			label: "Week"
			window: panel.usage.week
		}
	}

	component LimitBar: ColumnLayout {
		id: bar
		property string label
		property var window: ({ known: false, used: 0, reset: "" })
		readonly property real used: window.known ? window.used : 0

		Layout.fillWidth: true
		spacing: 4

		RowLayout {
			Layout.fillWidth: true
			Text {
				text: bar.label
				color: "#e3e7ed"
				font.pixelSize: 11
			}
			Item { Layout.fillWidth: true }
			Text {
				text: bar.window.known ? bar.window.reset : "unknown"
				color: "#7d8693"
				font.pixelSize: 10
			}
		}

		Rectangle {  // track
			id: track
			Layout.fillWidth: true
			implicitHeight: 8
			radius: 4
			color: "#2a2f37"
			border.color: "#343943"

			Rectangle {  // used part
				width: Math.max(bar.used > 0 ? height : 0, track.width * bar.used)
				height: parent.height
				radius: 4
				color: bar.used >= 0.9 ? "#f28b82" : bar.used >= 0.7 ? "#e5b567" : "#72a7ff"
				Behavior on width { NumberAnimation { duration: 300; easing.type: Easing.OutCubic } }
			}

			MouseArea {
				id: barMouse
				anchors.fill: parent
				hoverEnabled: true
			}
			ToolTip.visible: barMouse.containsMouse && bar.window.known
			ToolTip.text: Math.round(bar.used * 100) + " % of the " + bar.label.toLowerCase()
				+ " limit used"
		}
	}
}
