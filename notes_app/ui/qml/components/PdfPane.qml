import QtQuick
import QtQuick.Controls
import QtQuick.Pdf

// The PDF preview: pages stacked on a dark background.
// A plain ListView (instead of PdfMultiPageView) so the scroll position can
// be kept exactly when the PDF is rebuilt.
Rectangle {
	id: pane
	color: "#121418"

	readonly property bool hasPdf: notes.pdfUrl.toString() !== ""
	property real zoom: 1.0
	property real savedY: 0
	property bool restoring: false

	PdfDocument {
		id: pdf
		onStatusChanged: {
			if (pdf.status === PdfDocument.Ready && pane.restoring) {
				pane.restoring = false
				Qt.callLater(function() {
					pages.contentY = Math.min(pane.savedY, Math.max(0, pages.contentHeight - pages.height))
				})
			}
		}
	}

	// The revision in the query makes the URL change whenever the file is
	// rewritten, so PdfDocument reloads it (the query is ignored for files).
	function sourceUrl() {
		return notes.pdfUrl.toString() + "?rev=" + notes.pdfRevision
	}

	function update() {
		if (!hasPdf)
			return  // keep the old document loaded but hidden; no empty source
		const sameFile = pdf.source.toString().split("?")[0] === notes.pdfUrl.toString()
		savedY = sameFile ? pages.contentY : 0
		restoring = sameFile
		pdf.source = sourceUrl()
	}

	Connections {
		target: notes
		function onPdfChanged() { pane.update() }
	}

	Component.onCompleted: update()

	ListView {
		id: pages
		objectName: "pdfPages"
		anchors.fill: parent
		visible: pane.hasPdf && pdf.status === PdfDocument.Ready
		clip: true
		spacing: 14
		topMargin: 16
		bottomMargin: 16
		model: pdf.status === PdfDocument.Ready ? pdf.pageCount : 0
		boundsBehavior: Flickable.StopAtBounds
		ScrollBar.vertical: ScrollBar {}

		delegate: Item {
			id: pageItem
			required property int index
			readonly property size pointSize: pdf.pagePointSize(index)
			width: pages.width
			height: page.height

			Rectangle {  // soft shadow
				x: page.x + 2
				y: 3
				width: page.width
				height: page.height
				color: "#0a0b0d"
				opacity: 0.6
			}
			Rectangle {  // paper
				anchors.fill: page
				color: "white"
			}
			PdfPageImage {
				id: page
				document: pdf
				currentFrame: pageItem.index
				anchors.horizontalCenter: parent.horizontalCenter
				width: Math.round((pages.width - 32) * pane.zoom)
				height: Math.round(width * pageItem.pointSize.height / Math.max(1, pageItem.pointSize.width))
				sourceSize.width: width * Screen.devicePixelRatio
				sourceSize.height: height * Screen.devicePixelRatio
				fillMode: Image.PreserveAspectFit
				asynchronous: true
				cache: false
			}
		}

		// Ctrl + wheel zooms
		WheelHandler {
			acceptedModifiers: Qt.ControlModifier
			onWheel: function(event) {
				pane.zoom = Math.max(0.5, Math.min(2.5, pane.zoom * (event.angleDelta.y > 0 ? 1.1 : 1 / 1.1)))
			}
		}
	}

	Text {
		anchors.centerIn: parent
		width: parent.width - 60
		visible: !pages.visible
		horizontalAlignment: Text.AlignHCenter
		wrapMode: Text.WordWrap
		color: "#7d8693"
		font.pixelSize: 13
		text: notes.busy ? "Formatting…"
			: notes.currentPath === "" ? ""
			: "No PDF yet.\nPress Ctrl+Enter to format your notes."
	}
}
