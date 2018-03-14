import sys
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QApplication, QListWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QSlider, QAbstractItemView, QCheckBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from pathplan.path_planner import plan_path
from pathplan.plots import plot2d
from main import generate_path


class Gui(QWidget):

    def __init__(self):
        super(Gui, self).__init__()
        #Of the form {'path_name': {'param':val}}

        #TODO Set to some default params
        self.default_params = 'filename for default'
        self.current_params = json.load(open('default_params'))
        self.params = {}
        self.paths = {}
        self.start_dialogs()

        self.fig = Figure()

        self.ax = self.fig.add_subplot(111)

        self.init_ui()
        self.sample_plot()

    def load_lines(self):
        _,_,_,_, tc = load_test_case(self.test_case)
        return json.load(open(tc['lines']))

    def change_selected_paths(self):
        selected_items = self.path_list.selectedItems()
        self.current_paths = []
        for item in selected_items:
            text = str(item.text())
            self.current_paths.append((text, self.paths[text]))
      
        first = selected_items[0]
        text = str(first.text())
        self.current_parms = self.params[text]
        self.reset_parms(self.current_params, self.parm_vbox)
        
        self.plot(*self.current_paths)

    def get_special_path(self, name):
        return load_lines(self)
        

    def set_checkboxes(self, vbox, imax_3d=False):
        if not imax_3d:
            self.surface_checkbox = QCheckBox("Show Surface")
            vbox.addWidget(self.surface_checkbox)
            self.flight_checkbox = QCheckBox("Show Flight (if available)")
            vbox.addWidget(self.flight_checkbox)
            self.lidar_checkbox = QCheckBox("Lidar Penetration View")
            vbox.addWidget(self.lidar_checkbox)
            self.canopy_checkbox = QCheckBox("Show Canopy")
            vbox.addWidget(self.canopy_checkbox)
        else:
            pass


    def plot_lidar_penetration(self, path, surface, lidar):
        pass

    def special_path_check(self, name):
        if self.surface_checkox.isChecked():
            self.current_paths = [path for path in self.current_paths if path[0] != name]
        else:
            self.current_paths.append((name, self.get_special_path(name))

    def start_dialogs(self):
        fname = QFileDialog.getOpenFileName(self, 'Load In Test Case File', '/home')
         
        if fname[0]:
            paths['initial'] = generate_path(fname[1], 'test path', self.default_params)
            self.test_case = fname
            self.surface = 
        else:
            have_val, self.be_dem = QFileDialog.getOpenFileName(self, 'Bare Earth DEM', '/home')

            if not have_val:
                self.start_dialogs()
                return
            else:
                have_val, self.canopy_dem = QFileDialog.getOpenFileName(self, 'Canopy DEM', '/home')

                if not have_val:
                    self.start_dialogs()
                    return
                else:
                    have_val, self.path_file = QFileDialog.getOpenFileName(self, 'Initial Path', '/home')
                    if have_val:
                        self.start_dialogs()
                        return
                    self.test_case = self.path_file + ".test"
                    create_test_case(self.path_file+".test", self.be_dem, self.path_file, True, 'doesnt matter')
                    self.paths['initial'] = generate_path(self.path_file+".test", initial, self.current_params)
                    self.params['initial'] = self.current_params
          

    def plot(self, *paths):
        self.ax.clear()
        plot2d(*paths, ax=self.ax)
        
    def reset_parms(self, parm, vbox):
        for param,val in parm.items():
            label = QLabel(self.param_list)
            label.setText("{0}: {1}".format(param, val))
            vbox.addWidget(label)
            slider = QSlider(Qt.Horizontal)
            slider.setFocusPolicy(Qt.StrongFocus)
            slider.setTickPosition(QSlider.TicksBothSides)
            slider.setSingleStep(1)
            slider.setTickInterval(10)
            vbox.addWidget(slider)
        


    def init_ui(self):
        grid = QGridLayout()

        self.plotter = FigureCanvas(self.fig)

        self.path_list = QListWidget(self)
  
        self.path_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.metric_printout = QTextEdit(self)
        self.metric_printout.setReadOnly(True)


        for p in self.paths:
            self.path_list.addItem(p)

        self.param_list = QWidget()
        self.parm_vbox = QVBoxLayout()

        title = QLabel(self.param_list)
        title.setText("Parameter List")
        vbox.addWidget(title)

        self.reset_parms(self.current_params, self.parm_vbox)
 
        self.set_checkboxes(vbox)

        self.param_list.setLayout(self.parm_vboxvbox)

        grid.addWidget(self.plotter, 0, 0)
        grid.addWidget(self.path_list, 1, 1)
        grid.addWidget(self.param_list, 0, 1)
        grid.addWidget(self.metric_printout, 1, 0)
        self.setLayout(grid)
        self.show()

    def sample_plot(self):
        xs = list(range(0, 30))
        ys = list(range(2, 32))

        self.ax.clear()
        self.ax.plot(xs, ys)


if __name__ =='__main__':
    app = QApplication(sys.argv)
    gui = Gui()
    sys.exit(app.exec_())
