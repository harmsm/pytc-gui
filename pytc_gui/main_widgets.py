__description__ = \
"""
"""
__author__ = "Hiranmyai Duvvuri"
__date__ = "2017-01-06"

from . import boxes
from .qlogging_handler import OutputStream

from pytc.global_fit import GlobalFit

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import sys, inspect

class GUIMaster(QWidget):
    """
    Main class that holds all of the fitter sub-widgets.
    """

    def __init__(self, parent):

        super().__init__()

        self._parent = parent

        self._fitter = parent._fitter
        self._fitter_list = parent._fitter_list

        # Create a dictionary of GlobalFitOptions
        fit_args = inspect.getargspec(GlobalFit().fit)
        self._global_fit_options = {arg: param for arg, param
                                    in zip(fit_args.args[1:],fit_args.defaults)}

        # Lay out the widget.
        self.layout()

    def layout(self):
        """
        Create the widget layout.
        """

        # ------------ Plot widget ----------------------- 
        self._plot_box = boxes.PlotBox(self)

        # ------------ Experiments widget ----------------
        self._exp_box = boxes.ExperimentBox(self)
    
        # ------------ "Do fit" button -------------------
        do_fit_button = QPushButton("Do fit", self)
        do_fit_button.clicked.connect(self.do_fit_callback)

        # -------------- message box ---------------------
        self._message_box = QTextEdit()
        self._message_box.setReadOnly(True)

        scroll = QScrollArea(self)
        scroll.setWidget(self._message_box)
        scroll.setWidgetResizable(True)

        # redirect stdout to the message box
        self._temp = sys.stdout
        sys.stdout = OutputStream()
        sys.stdout.text_printed.connect(self.read_stdout_callback)

        # Split up the main window in a useful way

        # Split window vertically
        v_splitter = QSplitter(Qt.Vertical)
        v_splitter.addWidget(self._plot_box)
        v_splitter.addWidget(scroll)
        v_splitter.setSizes([300, 50])

        # now split horizontally
        h_splitter = QSplitter(Qt.Horizontal)
        h_splitter.addWidget(v_splitter)
        h_splitter.addWidget(self._exp_box)
        h_splitter.setSizes([200, 200])

        # Now add the split up window.
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(h_splitter)
        main_layout.addWidget(do_fit_button)

        # MJH ??? --> what is signaling architecture?
        self._parent.fit_signal.connect(self.fit_signal_update)

    def clear(self):
        """
        Clear the plot and experiment frames.
        """

        self._plot_box.clear()
        self._exp_box.clear()

    def update_fit_options(self, options_dict):
        """
        """
        self._global_fit_options = options_dict

    def do_fit_callback(self):
        """
        """
        self._exp_box.perform_fit(self._global_fit_options)
        self._plot_box.update()

    @pyqtSlot(GlobalFit)
    def fit_signal_update(self, obj):
        """
        """
        self._plot_box._fitter = obj
        self._exp_box._fitter = obj

    @pyqtSlot(str)
    def read_stdout_callback(self, text):
        """
        Wirte standard out to the main message box.
        """
        self._message_box.insertPlainText(text)

    @property
    def parent(self):
        """
        Parent window.
        """
        return self._parent

    @property
    def plot_box(self):
        """
        Main plot box.
        """ 
        return self._plot_box

    @property
    def exp_box(self):
        """
        Main experiment box.
        """
        return self._exp_box

    @property
    def message_box(self):
        """
        Main message box.
        """
        return self._message_box

    @property
    def fitter(self):
        """
        Main fitter object.
        """
        return self._fitter


