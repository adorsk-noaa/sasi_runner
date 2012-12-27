from sasi_runner.tasks.run_sasi_task import RunSasiTask
from javax.swing import (JPanel, JScrollPane, JTextArea, JFrame, JFileChooser,
                         JButton, WindowConstants, JLabel, BoxLayout)
from javax.swing.filechooser import FileNameExtensionFilter
from java.awt import (Component, BorderLayout)
import os
import tempfile
import logging
from sqlalchemy import create_engine
import shutil


class FnLogHandler(logging.Handler):
    """ Custom handler to send log messages to a given function. """
    def __init__(self, fn, **kwargs):
        logging.Handler.__init__(self, **kwargs)
        self.fn = fn

    def emit(self, record):
        try:
            self.fn(self.format(record))
        except:
            self.handleError(record)

class JythonGui(object):
    def __init__(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="sasi_runner.")
        self.db_file = os.path.join(self.tmp_dir, "sasi_runner.db")

        self.selected_input_file = None
        self.selected_output_file = None

        self.frame = JFrame(
            "SASI Runner",
            defaultCloseOperation = WindowConstants.EXIT_ON_CLOSE,
        )
        self.frame.size = (650, 400,)

        self.main_panel = JPanel()
        self.main_panel.layout = BoxLayout(self.main_panel, BoxLayout.Y_AXIS)
        self.frame.add(self.main_panel)

        # Select input panel.
        self.input_panel = JPanel()
        self.input_panel.alignmentX = Component.CENTER_ALIGNMENT
        self.main_panel.add(self.input_panel)
        self.input_panel.add(
            JLabel("1. Select a SASI .zip file or data folder:"))
        self.input_panel.add(
            JButton("Select input...", actionPerformed=self.openInputChooser))

        # Select output panel.
        self.output_panel = JPanel()
        self.output_panel.alignmentX = Component.CENTER_ALIGNMENT
        self.main_panel.add(self.output_panel)
        self.output_panel.add(JLabel("2. Specify an output file."))
        self.output_panel.add(
            JButton("Specify output...", actionPerformed=self.openOutputChooser))

        # Run panel.
        self.run_panel = JPanel()
        self.run_panel.alignmentX = Component.CENTER_ALIGNMENT
        self.main_panel.add(self.run_panel)
        self.run_message = JLabel("3. Run SASI:")
        self.run_panel.add(self.run_message)
        self.run_button = JButton("Run...", actionPerformed=self.runSASI)
        self.run_panel.add(self.run_button)

        # Log panel.
        self.log_panel = JPanel()
        self.log_panel.alignmentX = Component.CENTER_ALIGNMENT
        self.main_panel.add(self.log_panel)
        self.log_panel.setLayout(BorderLayout())
        self.log = JTextArea()
        self.log.editable = False
        self.logScrollPane = JScrollPane(self.log)
        self.logScrollPane.setVerticalScrollBarPolicy(
            JScrollPane.VERTICAL_SCROLLBAR_ALWAYS)
        self.log_panel.add(self.logScrollPane, BorderLayout.CENTER)

        # File selectors
        self.inputChooser = JFileChooser()
        self.inputChooser.fileSelectionMode = JFileChooser.FILES_AND_DIRECTORIES
        self.outputChooser = JFileChooser()
        self.outputChooser.fileSelectionMode = JFileChooser.FILES_ONLY

        self.frame.visible = True
        self.frame.setLocationRelativeTo(None)

    def log_msg(self, msg):
        self.log.append(msg + "\n")

    def openInputChooser(self, event):
        ret = self.inputChooser.showOpenDialog(self.frame)
        if ret == JFileChooser.APPROVE_OPTION:
            self.selected_input_file = self.inputChooser.selectedFile
            self.log_msg("Selected '%s' as input." % self.selected_input_file.path)

    def openOutputChooser(self, event):
        ret = self.outputChooser.showSaveDialog(self.frame)
        if ret == JFileChooser.APPROVE_OPTION:
            self.selected_output_file = self.outputChooser.selectedFile
            self.log_msg(
                "Selected '%s' as output." % self.selected_output_file.path)

    def runSASI(self, event):
        try:
            self.validateParameters()
        except Exception as e:
            self.log_msg("ERROR: '%s'" % e)


        logger = logging.getLogger('sasi_runner_gui')
        logger.addHandler(logging.StreamHandler())
        def log_fn(msg):
            self.log_msg(msg)
        logger.addHandler(FnLogHandler(log_fn))
        logger.setLevel(logging.DEBUG)

        def get_connection():
            engine = create_engine('h2+zxjdbc:////%s' % self.db_file)
            con = engine.connect()
            return con

        task = RunSasiTask(
            #input_path=self.selected_input_file.path,
            #output_file=self.selected_output_file.path,
            input_path="/home/adorsk/projects/sasi_runner/lib/sasi_runner/tasks/test_data/reduced_test_data",
            output_file="/home/adorsk/Desktop/foo.tar.gz",
            logger=logger,
            get_connection=get_connection,
            config={
                'run_model': {
                    'commit_interval': 1000,
                }
            }
        )
        task.call()
        shutil.rmtree(self.tmp_dir)

    def validateParameters(self):
        return True

def main():
    JythonGui()

if __name__ == '__main__':
    main()
