from javax.swing import (JPanel, JScrollPane, JTextArea, JFrame, JFileChooser,
                         JButton, WindowConstants, JLabel, BoxLayout)
from java.awt import Component


class SwingTest(object):
    def __init__(self):
        self.frame = JFrame(
            "SASI Runner",
            defaultCloseOperation = WindowConstants.EXIT_ON_CLOSE,
        )
        self.frame.size = (800, 800,)

        self.main_panel = JPanel()
        self.main_panel.layout = BoxLayout(self.main_panel, BoxLayout.Y_AXIS)
        self.frame.add(self.main_panel)

        # Select panel.
        self.select_panel = JPanel()
        self.select_panel.alignmentX = Component.CENTER_ALIGNMENT
        self.main_panel.add(self.select_panel)
        self.select_message = JLabel("1. Select a SASI .zip file or data folder:")
        self.select_panel.add(self.select_message)
        self.fc = JFileChooser()
        self.open_button = JButton("Select...", actionPerformed=self.openFileChooser)
        self.select_panel.add(self.open_button)

        # Run panel.
        self.run_panel = JPanel()
        self.run_panel.alignmentX = Component.CENTER_ALIGNMENT
        self.main_panel.add(self.run_panel)
        self.run_message = JLabel("2. Run SASI:")
        self.run_panel.add(self.run_message)
        self.run_button = JButton("Run...", actionPerformed=self.runSASI)
        self.run_panel.add(self.run_button)

        # Log panel.
        self.log_panel = JPanel()
        self.log_panel.alignmentX = Component.CENTER_ALIGNMENT
        self.main_panel.add(self.log_panel)
        self.log = JTextArea(5,20)
        self.log.editable = False
        self.logScrollPane = JScrollPane(self.log)
        self.log_panel.add(self.logScrollPane)
        
        self.frame.pack()
        self.frame.visible = True

        for i in range(10):
            self.log_msg(str(i))
            self.log.caretPosition = self.log.document.length

    def log_msg(self, msg):
        self.log.append(msg + "\n")

    def openFileChooser(self, event):
        self.log_msg("openinig...")
        ret = self.fc.showOpenDialog(self.frame)
        if ret == JFileChooser.APPROVE_OPTION:
            selected_file = self.fc.selectedFile
            self.log_msg("fname: %s" % selected_file.name)

    def runSASI(self, event):
        pass

def main():
    SwingTest()

if __name__ == '__main__':
    main()
