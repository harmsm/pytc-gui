from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import pytc
import inspect, math

class Sliders(QWidget):
    """
    create sliders for an experiment
    """

    def __init__(self, param_name, parent):
        super().__init__()

        self._exp = parent._exp
        self._param_name = param_name
        self._fitter = parent._fitter
        self._fit_run = False
        self._main_box = parent._main_box
        self._plot_frame = parent._plot_frame

        self.layout()

    def bounds(self):
        """
        """
        pass

    @property
    def name(self):
        """
        """
        return self._param_name

    def layout(self):
        """
        """
        self._main_layout = QGridLayout(self)
        self._main_layout.setVerticalSpacing(40)

        self._name_label = QLabel(self._param_name, self)
        self._main_layout.addWidget(self._name_label, 0, 0, 0, 2)

        self._fix = QCheckBox("Fix?", self)
        self._fix.toggle()
        self._fix.setChecked(False)
        self._fix.stateChanged.connect(self.fix_layout)
        self._main_layout.addWidget(self._fix, 1, 0)

        self._slider = QSlider(Qt.Horizontal)
        self._slider.sliderReleased.connect(self.update_val)
        self._main_layout.addWidget(self._slider, 1, 1)
        self._slider.setMinimumWidth(100)

        self._param_guess_label = QLabel("", self)
        self._main_layout.addWidget(self._param_guess_label, 1, 2)

        self.bounds()

        self._fix_int = QLineEdit(self)
        self._main_layout.addWidget(self._fix_int, 1, 3)
        self._fix_int.setText(str(1))
        self._fix_int.returnPressed.connect(self.fix)
        self._fix_int.hide()

        # need to fix
        self._update_min_label = QLabel("min: ", self)
        self._main_layout.addWidget(self._update_min_label, 1, 4)

        self._update_min = QLineEdit(self)
        self._main_layout.addWidget(self._update_min, 1, 5)
        self._update_min.returnPressed.connect(self.min_bounds)
        self._update_min.setFixedWidth(60)

        self._update_max_label = QLabel("max: ", self)
        self._main_layout.addWidget(self._update_max_label, 1, 6)

        self._update_max = QLineEdit(self)
        self._main_layout.addWidget(self._update_max, 1, 7)
        self._update_max.returnPressed.connect(self.max_bounds)
        self._update_max.setFixedWidth(60)

        self._main_box.fit_signal.connect(self.set_fit_true)

    @pyqtSlot()
    def set_fit_true(self):
        """
        """
        self._fit_run = True

    def check_if_fit(self):
        """
        if a fit has been run, and a slider is changed, change all parameters back to guesses in slider widgets
        """
        if self._fit_run:
            self._fitter.guess_to_value()
            self._plot_frame.update()
            self._fit_run = False

    def fix_layout(self, state):
        """
        initial parameter fix and updating whether slider/fixed int is hidden or shown
        """
        if state == Qt.Checked:
            # change widget views
            self._fix_int.show()
            self._slider.hide()
            self._fitter.update_fixed(self._param_name, int(self._fix_int.text()), self._exp)
            self.check_if_fit()
        else:
            #change widget views
            self._fix_int.hide()
            self._slider.show()

            self._fitter.update_fixed(self._param_name, None, self._exp)

    def fix(self):
        """
        update fixed value when enter/return key pressed
        """
        try:
            self._fitter.update_fixed(self._param_name, int(self._fix_int.text()), self._exp)
            self.check_if_fit()
        except:
            pass

    def update_val(self):
        """
        update value for parameter based on slider value
        """

        value = int(self._slider.value())

        self._param_guess_label.setText(str(value))

        # transform values back
        if self._range_diff < 10:
            value /= 10
        elif self._range_diff < 100000:
            value *= 100
        elif self._range_diff < 100000000:
            value = 10 ** value

        print(value)

        if value != 0:
            # if guess update, update parameter as well for plot
            self._fitter.update_guess(self._param_name, value, self._exp)
            self._fitter.update_value(self._param_name, value, self._exp)
        else:
            pass

        self.check_if_fit()

    def transform_forward(self, val):
        """
        transform values for use in slider
        """
        if self._range_diff < 10:
            slider = val * 10
        elif self._range_diff < 100000:
            slider = val / 100
        elif self._range_diff < 100000000:
            slider = math.log10(val)

        return slider

    def min_bounds(self):
        """
        update the minimum bounds when enter/return key pressed
        """
        try:
            self._min = int(self._update_min.text())

            # make sure K min bound isn't negative
            if "K" in self._param_name and self._min < 0:
                self._min = 1
                print("K cannot be negative", self._min)

            # set new range
            self._range_diff = self._max - self._min

            # if range has significantly changed, update value transformations
            self._slider_max = self.transform_forward(self._max)
            self._slider_min = self.transform_forward(self._min)

            # set slider min
            self._slider.setMinimum(self._slider_min)
            self.update_bounds()

            print("min bound updated: " + value)
        except:
            print('invalid value')

    def max_bounds(self):
        """
        update maximum bounds when enter/return key pressed
        """
        try:
            self._max = int(self._update_max.text())

            # set new range
            self._range_diff = self._max - self._min

            # if range has significantly changed, update the value transformations
            self._slider_max = self.transform_forward(self._max)
            self._slider_min = self.transform_forward(self._min)

            # set slider max
            self._slider.setMaximum(self._slider_max)
            self.update_bounds()

            print("max bound updated: " + value)
        except:
            pass

    def update_bounds(self):
        """
        update min/max bounds and check if range needs to be updated as well
        """
        pass