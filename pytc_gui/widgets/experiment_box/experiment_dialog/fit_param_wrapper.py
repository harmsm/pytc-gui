__description__ = \
"""
Create GUI elements wrapping a single fit parameter.
"""
__author__ = "Michael J. Harms"
__date__ = "2017-06-01"

from .connector_dialog import AddConnectorDialog
from .global_dialog import AddGlobalDialog

from PyQt5 import QtWidgets as QW
from PyQt5 import QtCore as QC

class FitParamWrapper(QW.QWidget):
    """
    This class wraps a single fit parameter with a gui. 
    """

    def __init__(self,parent,fit,experiment,fit_param,float_view_cutoff=100000.):
        """
        Initialize the class.

        parent: parent widget
        fit: FitContainer object
        experiment: pytc.ITCExperiment instance
        fit_param: pytc.FitParameter instance to wrap
        float_view_cutoff: how to show floats in QLineEdit boxes
        """

        super().__init__()

        self._parent = parent
        self._fit = fit
        self._experiment = experiment
        self._p = fit_param
        self._float_view_cutoff = float_view_cutoff       

        self._fit.fit_changed_signal.connect(self.fit_has_changed_slot)

        # This is the index for the experiment in the global fit object
        self._expt_index = self._fit.experiments.index(self._experiment)
 
        self._is_connector_param = False
        self._is_connected = False

        self.layout()


    def layout(self):

        # --------------- Guess -----------------       
        self._guess = QW.QLineEdit()
        self._guess.textChanged.connect(self._guess_check_handler)
        self._guess.editingFinished.connect(self._guess_final_handler)

        # --------------- Lower -----------------       
        self._lower = QW.QLineEdit()
        self._lower.textChanged.connect(self._lower_check_handler)
        self._lower.editingFinished.connect(self._lower_final_handler)
               
        # --------------- Upper -----------------       
        self._upper = QW.QLineEdit()
        self._upper.textChanged.connect(self._upper_check_handler)
        self._upper.editingFinished.connect(self._upper_final_handler)

        # --------------- Fixed -----------------
        self._fixed = QW.QCheckBox()
        self._fixed.stateChanged.connect(self._fixed_handler)
       
        # --------------- Alias -----------------
        self._alias = QW.QComboBox()
        self._alias.addItem("Unlink")
        self._alias.addItem("Add global")
        self._alias.addItem("Add connector")

        self._alias.currentIndexChanged.connect(self._alias_handler)
    
        # Load in parameters from FitParameter object
        self.update()
        

    def _guess_check_handler(self,set_value=False):
        """
        Handle guess entries.  Turn pink of the value is bad.  

        set_value: whether to set the underlying value.
        """

        success = True 
        try:
            value = float(self._guess.text())
            if value < self._p.bounds[0] or value > self._p.bounds[1]:
                raise ValueError
        except ValueError:
            success = False    
 
        if success:
            color = "#FFFFFF"
        else:
            color = "#FFB6C1"

        self._guess.setStyleSheet("QLineEdit {{ background-color: {} }}".format(color))

        if success and set_value:
            self._p.guess = value
            if self._fit.continuous_update:
                self._fit.emit_changed()

        # Record instance-wide value indiciating whether the current guess is 
        # valid or not. 
        if success:
            self._current_guess_is_good = True
        else:
            self._current_guess_is_good = False

    def _guess_final_handler(self):
        """
        Run check, then set value.
        """

        self._guess_check_handler(set_value=True) 
        
    def _lower_check_handler(self,set_value=False):
        """
        Handle lower bound entries.  Turn pink of the value is bad.  

        set_value: whether to set the underlying value.
        """

        success = True 
        try:
            value = float(self._lower.text())
            if value > self._p.guess:
                raise ValueError
        except ValueError:
            success = False    
 
        if success:
            color = "#FFFFFF"
        else:
            color = "#FFB6C1"

        self._lower.setStyleSheet("QLineEdit {{ background-color: {} }}".format(color))

        if success and set_value:
            self._p.bounds = [value,self._p.bounds[1]]
            if self._fit.continuous_update:
                self._fit.emit_changed()

    def _lower_final_handler(self):
        """
        Run check, then set value.
        """
        self._lower_check_handler(set_value=True)

    def _upper_check_handler(self,set_value=False):
        """
        Handle upper bound entries.  Turn pink of the value is bad.  

        set_value: whether to set the underlying value.
        """

        success = True 
        try:
            value = float(self._upper.text())
            if value < self._p.guess:
                raise ValueError
        except ValueError:
            success = False    
 
        if success:
            color = "#FFFFFF"
        else:
            color = "#FFB6C1"

        self._upper.setStyleSheet("QLineEdit {{ background-color: {} }}".format(color))
     
        if success and set_value:
            self._p.bounds = [self._p.bounds[0],value] 
            if self._fit.continuous_update:
                self._fit.emit_changed()
    
    def _upper_final_handler(self):
        """
        Run check, then set value.
        """
        self._upper_check_handler(set_value=True)
 
    def _fixed_handler(self):
        """
        Handle fixing parameters.
        """
   
        value = self._fixed.checkState()
 
        # If false, immediately record    
        if not value:
            self._p.fixed = value
    
        else:
            
            # Make sure the guess is okay before setting to true
            self._guess_check_handler()
            if self._current_guess_is_good:
                fixed_value = float(self._guess.text()) 
            
                self._p.fixed = True
                self._p.guess = fixed_value
                self._p.value = fixed_value

            else:
                err = "Fixing variable requires valid guess. (Guess will become fixed value).\n"
                error_message = QW.QMessageBox.warning(self._parent,"warning",err,QW.QMessageBox.Ok)
                self._fixed.setCheckState(False)

    def _alias_handler(self,value):
        """
        Handle changes to alias ComboBox.
        """

        value = self._alias.currentText()

        # unlink variable
        if value == "Unlink":

            # Remove current global link, if present
            try:
                self._fit.fitter.unlink_from_global(self._experiment,self._p.name)
            except (KeyError,ValueError):
                pass

            self.set_as_connected(False)
            self._fit.emit_changed()

        # add new global parameter
        elif value == "Add global":
            self._tmp = AddGlobalDialog(self,self._fit,self._experiment,self._p)
            self._tmp.show() 

        # add new connector
        elif value == "Add connector":
            self._tmp = AddConnectorDialog(self,self._fit,self._experiment,self._p)
            self._tmp.show()

        # variable connected programmatically, not by user.  change nothing
        elif value == "connected":
            return

        # They've selected something dynamically added to the ComboBox
        else:
    
            # They've selected an existing global variable
            if value in self._fit.fitter.global_param.keys():

                # Remove current global link, if present
                try:
                    self._fit.fitter.unlink_from_global(self._experiment,self._p.name)
                except KeyError:
                    pass
                self._fit.fitter.link_to_global(self._experiment,self._p.name,value) 

            # They've selected an existing connector method
            else:
                
                # Remove current global link, if present
                try:
                    self._fit.fitter.unlink_from_global(self._experiment,self._p.name)
                except KeyError:
                    pass

                method = self._fit.connector_methods[value]
                if method in self._experiment.model.param_aliases.values():

                    warn = "connector method can only be assigned to one parameter per experiment."
                    error_message = QW.QMessageBox.warning(self, "warning", warn, QW.QMessageBox.Ok)

                    alias_index = self._alias.findText("Unlink") 
                    self._alias.setCurrentIndex(alias_index)
                    self.set_as_connected(False)
                    self._fit.emit_changed()
                    return

                # Create new connection
                self._fit.fitter.link_to_global(self._experiment,self._p.name,method)
                self.set_as_connected(True)

        self._fit.emit_changed()
       
    @QC.pyqtSlot(bool)
    def fit_has_changed_slot(self):
        self.update()

    def update(self):
        """
        Update all of the widgets.
        """

        # Pause updates while all of these widgets update
        self._fit.pause_updates(True)

        # Update guess, lower, upper, and fixed.  This is not done for
        # parameters that are linked to connector methods.
        if not self._is_connected:
        
            # --------------- Guess -----------------
            if self._p.guess < 1/self._float_view_cutoff or self._p.guess > self._float_view_cutoff:
                guess_str = "{:.8e}".format(self._p.guess)
            else:
                guess_str = "{:.8f}".format(self._p.guess)
            self._guess.setText(guess_str)

            # --------------- Lower -----------------
            if self._p.bounds[0] < 1/self._float_view_cutoff or self._p.bounds[0] > self._float_view_cutoff:
                lower_str = "{:.8e}".format(self._p.bounds[0])
            else:
                lower_str = "{:.8f}".format(self._p.bounds[0])
            self._lower.setText(lower_str)

            # --------------- Upper -----------------
            if self._p.bounds[1] < 1/self._float_view_cutoff or self._p.bounds[1] > self._float_view_cutoff:
                upper_str = "{:.8e}".format(self._p.bounds[1])
            else:
                upper_str = "{:.8f}".format(self._p.bounds[1])
            self._upper.setText(upper_str)

            # --------------- Fixed -----------------
            self._fixed.setChecked(self._p.fixed)

        # Update the alias ComboBox.  This is not done if the parameter is a 
        # connector fit parameter.
        if not self._is_connector_param:       
 
            # ------------- alias -----------------

            global_param = list(self._fit.global_param.keys())

            # global variables we *don't* want in our alias dropdown.  They
            # are tied into connector instance.
            global_connector_variables = [] 

            # Go through all connectors
            params_to_keep = [] 
            for c in self._fit.connectors:
          
                connector_methods = []
                connector_methods.extend(c.local_methods.keys())
                global_connector_variables.extend(c.params.keys())

                # If any of the global_connector_variables are in the 
                # global_params, it says that the connector is still alive.  
                # That means keep the connector.
                connector_found = False
                for p in global_connector_variables:
                    if p in global_param:
                        params_to_keep.extend(c.local_methods.keys())

            # These guys should always be kept
            params_to_keep.append("Unlink")
            params_to_keep.append("Add global")
            params_to_keep.append("Add connector")
  
            # Grab every global parameter that is *not* a global connector 
            # parameter
            for p in global_param:
                if p not in global_connector_variables:
                    params_to_keep.append(p)
 
            # Make sure params_to_keep are unique after all that
            params_to_keep = list(set(params_to_keep))
    
            # Make sure all of the global parameters are in the dropdown
            for p in params_to_keep:
                if self._alias.findText(p) == -1:
                    self._alias.addItem(p)
    
            # Remove anything not in params_to_keep
            indexes = list(range(self._alias.count()))
            indexes.reverse() 
            for i in indexes:
                item_text = self._alias.itemText(i)
                if item_text not in params_to_keep:
                    self._alias.removeItem(i)

            # Now grab the current alias for this parameter
            param_aliases = self._fit.fitter.param_aliases[1][self._expt_index]
            try:
                current_alias = param_aliases[self._p.name]
                if type(current_alias) is not str:

                    # if the alias is not a string, it is a connector method
                    current_alias = "{}.{}".format(current_alias.__self__.name,
                                                   current_alias.__name__)
            except KeyError:
                current_alias = "Unlink"
                self.set_as_connected(False)

            # Update the dropdown so it points to the correct parameter
            alias_index = self._alias.findText(current_alias) 
            self._alias.setCurrentIndex(alias_index)

        # Resume updates
        self._fit.pause_updates(False)

    def set_as_connector_param(self,is_connector_param):
        """
        Configure the widget as a connector parameter (cannot change global
        linkage).

        is_connector_param: True or False
        """

        self._is_connector_param = is_connector_param

        if is_connector_param:
            self._alias.addItem("connected")
            index = self._alias.findText("connected")
            self._alias.setCurrentIndex(index)
            self._alias.setDisabled(True)

        else:
            index = self._alias.findText("connected")
            if index != -1:
                self._alias.removeItem(index)
            self._alias.setDisabled(False)

    def set_as_connected(self,is_connected):
        """
        Set this widget into "connected-to-connector-method" state.  This 
        disables everything except the alias comboBox.

        is_connected: bool (whether in this state or not)
        """

        # Only do this if the status is changing
        if self._is_connected == is_connected:
            return

        self._is_connected = is_connected

        if self._is_connected:

            self._guess.setText("")
            self._guess.setDisabled(True)
            self._guess.setStyleSheet("QLineEdit {{ background-color: {} }}".format("#C0C0C0"))

            self._fixed.setChecked(False)
            self._fixed.setDisabled(True)

            self._lower.setText("")
            self._lower.setDisabled(True)
            self._lower.setStyleSheet("QLineEdit {{ background-color: {} }}".format("#C0C0C0"))

            self._upper.setText("")
            self._upper.setDisabled(True)
            self._upper.setStyleSheet("QLineEdit {{ background-color: {} }}".format("#C0C0C0"))

        else:
            self._guess.setText("")
            self._guess.setDisabled(False)

            self._fixed.setChecked(False)
            self._fixed.setDisabled(False)

            self._lower.setText("")
            self._lower.setDisabled(False)

            self._upper.setText("")
            self._upper.setDisabled(False)

            self.update()
     
    @property
    def guess_widget(self):
        return self._guess

    @property
    def lower_widget(self):
        return self._lower

    @property
    def upper_widget(self):
        return self._upper

    @property
    def fixed_widget(self):
        return self._fixed

    @property
    def alias_widget(self):
        return self._alias 

    @property
    def name(self):
        return self._p.name