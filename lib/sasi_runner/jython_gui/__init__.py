from sasi_runner.tasks.run_sasi_task import RunSasiTask
from javax.swing import (
    JPanel, JScrollPane, JTextArea, JFrame, JFileChooser, JButton, 
    WindowConstants, JLabel, BoxLayout, JTextField, SpringLayout, JCheckBox,
    JProgressBar
)
from javax.swing.filechooser import FileNameExtensionFilter
from javax.swing.border import EmptyBorder
from java.awt import (Component, BorderLayout, GridLayout)
from java.awt.event import (AdjustmentListener, ItemListener, ItemEvent)
from java.lang import System
from java.io import File
import spring_utilities as SpringUtilities
import os
import tempfile
import logging
import sqlalchemy_h2
from sqlalchemy import create_engine
import shutil
from threading import Thread


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

class JythonGui(ItemListener):
    def __init__(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="sasi_runner.")
        self.db_file = os.path.join(self.tmp_dir, "sasi_runner.db")

        self.logger = logging.getLogger('sasi_runner_gui')
        self.logger.addHandler(logging.StreamHandler())
        def log_fn(msg):
            self.log_msg(msg)
        self.logger.addHandler(FnLogHandler(log_fn))
        self.logger.setLevel(logging.DEBUG)

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

        self.top_panel = JPanel(SpringLayout())
        self.top_panel.alignmentX = Component.CENTER_ALIGNMENT
        self.main_panel.add(self.top_panel)

        # Select input elements.
        self.top_panel.add(
            JLabel("1. Select a SASI .zip file or data folder:"))
        self.top_panel.add(
            JButton("Select input...", actionPerformed=self.openInputChooser))

        # Select output elements.
        self.top_panel.add(JLabel("2. Specify an output file."))
        self.top_panel.add(
            JButton("Specify output...", actionPerformed=self.openOutputChooser))

        # Set result fields.
        result_fields = [
            {'id': 'gear_id', 'label': 'Gear', 'selected': True}, 
            {'id': 'substrate_id', 'label': 'Substrate', 'selected': False}, 
            {'id': 'energy_id', 'label': 'Energy', 'selected': False},
            {'id': 'feature_id', 'label': 'Feature', 'selected': False}, 
            {'id': 'feature_category_id', 'label': 'Feature Category', 
             'selected': False}
        ]
        self.selected_result_fields = {}
        self.top_panel.add(JLabel("3. Set result resolution."))
        checkPanel = JPanel(GridLayout(0, 1))
        self.top_panel.add(checkPanel) 
        self.resultFieldCheckBoxes = {}
        for result_field in result_fields:
            self.selected_result_fields.setdefault(
                result_field['id'], result_field['selected'])
            checkBox = JCheckBox(
                result_field['label'], result_field['selected'])
            checkBox.addItemListener(self)
            checkPanel.add(checkBox)
            self.resultFieldCheckBoxes[checkBox] = result_field

        # Run elements.
        self.run_message = JLabel("4. Run SASI:")
        self.top_panel.add(self.run_message)
        self.run_button = JButton("Run...", actionPerformed=self.runSASI)
        self.top_panel.add(self.run_button)

        SpringUtilities.makeCompactGrid(self.top_panel, 4, 2, 6, 6, 6, 6)

        # Progress bar.
        self.progressBar = JProgressBar(0, 100)
        self.main_panel.add(self.progressBar)

        # Log panel.
        self.log_panel = JPanel()
        self.log_panel.alignmentX = Component.CENTER_ALIGNMENT
        self.log_panel.setBorder(EmptyBorder(10,10,10,10))
        self.main_panel.add(self.log_panel)
        self.log_panel.setLayout(BorderLayout())
        self.log = JTextArea()
        self.log.editable = False
        self.logScrollPane = JScrollPane(self.log)
        self.logScrollPane.setVerticalScrollBarPolicy(
            JScrollPane.VERTICAL_SCROLLBAR_ALWAYS)
        self.logScrollBar = self.logScrollPane.getVerticalScrollBar()
        self.log_panel.add(self.logScrollPane, BorderLayout.CENTER)

        # File selectors
        self.inputChooser = JFileChooser()
        self.inputChooser.fileSelectionMode = JFileChooser.FILES_AND_DIRECTORIES
        self.outputChooser = JFileChooser()
        defaultOutputFile = os.path.join(System.getProperty("user.home"),
                                         "sasi_project.tgz")

        self.outputChooser.setSelectedFile(File(defaultOutputFile));
        self.outputChooser.fileSelectionMode = JFileChooser.FILES_ONLY

        self.frame.setLocationRelativeTo(None)
        self.frame.visible = True

    def itemStateChanged(self, event):
        """ Listen for checkbox changes. """
        checkBox = event.getItemSelectable()
        is_selected = (event.getStateChange() == ItemEvent.SELECTED)
        result_field = self.resultFieldCheckBoxes[checkBox]
        self.selected_result_fields[result_field['id']] = is_selected
        self.log_msg("srf: %s" % self.selected_result_fields)

    def log_msg(self, msg):
        """ Print message to log and scroll to bottom. """
        self.log.append(msg + "\n")
        self.log.setCaretPosition(self.log.getDocument().getLength())

    def openInputChooser(self, event):
        ret = self.inputChooser.showOpenDialog(self.frame)
        if ret == JFileChooser.APPROVE_OPTION:
            self.selected_input_file = self.inputChooser.selectedFile
            self.log_msg("Selected '%s' as input." % self.selected_input_file.path)

    def openOutputChooser(self, event):
        ret = self.outputChooser.showSaveDialog(self.frame)
        if ret == JFileChooser.APPROVE_OPTION:
            selectedPath = self.outputChooser.selectedFile.path
            if not selectedPath.endswith('.tgz'):
                tgzPath = selectedPath + '.tgz'
                self.outputChooser.setSelectedFile(File(tgzPath))
            self.selected_output_file = self.outputChooser.selectedFile
            self.log_msg(
                "Selected '%s' as output." % self.selected_output_file.path)

    def runSASI(self, event):
        try:
            self.validateParameters()
        except Exception as e:
            self.log_msg("ERROR: '%s'" % e)

        # Run task in a separate thread, so that log
        # messages will be shown as task progresses.
        def run_task():
            self.progressBar.setValue(0)
            self.progressBar.setIndeterminate(True)

            def get_connection():
                engine = create_engine('h2+zxjdbc:////%s' % self.db_file)
                con = engine.connect()
                return con

            try:
                # Set result fields.
                result_fields = []
                for field_id, is_selected in self.selected_result_fields.items():
                    if is_selected: result_fields.append(field_id)

                task = RunSasiTask(
                    input_path=self.selected_input_file.path,
                    output_file=self.selected_output_file.path,
                    logger=self.logger,
                    get_connection=get_connection,
                    config={
                        'result_fields': result_fields,
                        'run_model': {
                            'run': {
                                'batch_size': 'auto',
                            }
                        },
                        'output': {
                            'batch_size': 'auto',
                        },
                    }
                )
                task.call()
            except Exception as e:
                self.logger.exception("Could not complete task")

            self.progressBar.setIndeterminate(False)
            self.progressBar.setValue(100)

            shutil.rmtree(self.tmp_dir)

        Thread(target=run_task).start()

    def validateParameters(self):
        return True

def main():
    JythonGui()

if __name__ == '__main__':
    main()
