import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Asks for a name (Enter accepts, Esc cancels). Emits accepted(name).
Popup {
	id: popup

	property string title
	property string placeholder
	signal accepted(string name)

	anchors.centerIn: Overlay.overlay
	width: 340
	modal: true
	focus: true
	padding: 16
	closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

	onOpened: { field.text = ""; field.forceActiveFocus() }

	background: Rectangle {
		color: "#202329"
		border.color: "#383d46"
		radius: 8
	}
	Overlay.modal: Rectangle { color: "#80000000" }

	contentItem: ColumnLayout {
		spacing: 12

		Text {
			text: popup.title
			color: "#e3e7ed"
			font.pixelSize: 14
			font.bold: true
		}
		VTextField {
			id: field
			objectName: "nameField"
			Layout.fillWidth: true
			placeholderText: popup.placeholder
			onAccepted: popup.accepted(text)
		}
		RowLayout {
			Layout.alignment: Qt.AlignRight
			spacing: 8
			VButton { text: "Cancel"; onClicked: popup.close() }
			VButton {
				text: "Create"
				kind: "primary"
				enabled: field.text.trim() !== ""
				onClicked: popup.accepted(field.text)
			}
		}
	}
}
