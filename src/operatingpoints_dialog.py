from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QMessageBox, QHeaderView, QTableWidgetItem
from copy import deepcopy

import operatingpoints_ui
from operatingpoint_dialog import OperatingPointDialog
from operatingpoints import OperatingPoints, OperatingPoint, operatingpoints
from flaphingepoint_dialog import FlapHingePointDialog
from settings import xfoilsettings

class OperatingPointsDialog(QDialog):
    def __init__(self):
        super(OperatingPointsDialog, self).__init__()
        self.ui = operatingpoints_ui.Ui_Dialog()
        self.ui.setupUi(self)

        # Temporary storage of operating points
        self.points = OperatingPoints()
        self.points.setting("xflap").value = deepcopy(operatingpoints.value("xflap"))
        self.points.setting("yflap").value = deepcopy(operatingpoints.value("yflap"))
        self.points.setting("yflapSpecification").value = \
                    deepcopy(operatingpoints.value("yflapSpecification"))
        for i in range(operatingpoints.numPoints()):
            self.points.addPoint(deepcopy(operatingpoints.point(i)))

        # Resize behavior for headers
        self.ui.pointsTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # Signals and slots
        self.ui.addButton.clicked.connect(self.addPoint)
        self.ui.editButton.clicked.connect(self.editPoint)
        self.ui.deleteButton.clicked.connect(self.deletePoint)
        self.ui.pointsTable.cellDoubleClicked[int,int].connect(self.editPoint)
        self.ui.flapHingeButton.clicked.connect(self.setFlapHingePoint)

        # Populate table
        if self.points.numPoints() == 0:
            self.ui.editButton.setEnabled(False)
            self.ui.deleteButton.setEnabled(False)
        self.ui.pointsTable.setRowCount(0)
        for i in range(self.points.numPoints()):
            self.addRow(self.points.point(i))

    def reject(self):
        ret = QMessageBox.question(self, "Confirm close", "Any changes will be lost. " +
                                   "Are you sure you want to close this dialog?")
        if ret == QMessageBox.Yes:
            self.hide()
            self.setResult(QDialog.Rejected)

    # Gets row items from operating point
    def itemsFromOperatingPoint(self, operatingpoint):
        items = []
        items.append(QTableWidgetItem(operatingpoint.value("optimizationGoal")))
        if operatingpoint.value("specCondition") == "Cl":
            text = "Cl = {:.4f}".format(operatingpoint.value("condition"))
        else:
            text = "AoA = {:.4f}".format(operatingpoint.value("condition"))
        items.append(QTableWidgetItem(text))
        items.append(QTableWidgetItem("{:.4e}".format(operatingpoint.value("reynolds"))))
        items.append(QTableWidgetItem("{:.4f}".format(operatingpoint.value("mach"))))
        items.append(QTableWidgetItem("{:.4f}".format(operatingpoint.value("weighting"))))
        if operatingpoint.value("flapBehavior") == "No deflection":
            text = "None"
        elif operatingpoint.value("flapBehavior") == "Specified deflection":
            text = "{:.4f}".format(operatingpoint.value("flapDeflection"))
        elif operatingpoint.value("flapBehavior") == "Optimized deflection":
            text = "Optimized"
        items.append(QTableWidgetItem(text))
        if operatingpoint.value("ncritBehavior") == "Use Xfoil settings":
            text = "{:.4f}".format(xfoilsettings.value("ncrit"))
        else:
            text = "{:.4f}".format(operatingpoint.value("ncrit"))
        items.append(QTableWidgetItem(text))
        if operatingpoint.value("tripBehavior") == "Use Xfoil settings":
            textt = "{:.4f}".format(xfoilsettings.value("xtript"))
            textb = "{:.4f}".format(xfoilsettings.value("xtripb"))
        else:
            textt = "{:.4f}".format(operatingpoint.value("xtript"))
            textb = "{:.4f}".format(operatingpoint.value("xtripb"))
        items.append(QTableWidgetItem(textt))
        items.append(QTableWidgetItem(textb))

        # Set flags (to make them non-editable) and text alignment
        ncols = self.ui.pointsTable.columnCount()
        for i in range(len(items)):
            items[i].setTextAlignment(Qt.AlignCenter)
            items[i].setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        return items

    # Adds a row in the table
    def addRow(self, operatingpoint):
        nrows = self.ui.pointsTable.rowCount()
        self.ui.pointsTable.setRowCount(nrows+1)
        items = self.itemsFromOperatingPoint(operatingpoint)

        # Set items in table
        for i in range(len(items)):
            self.ui.pointsTable.setItem(nrows, i, items[i])

    def addPoint(self):
        dialog = OperatingPointDialog()
        dialog.setWindowTitle("New operating point")
        if dialog.exec():
            newpoint = dialog.operatingPoint()
            self.points.addPoint(deepcopy(newpoint))
            self.addRow(newpoint)
            self.ui.editButton.setEnabled(True)
            self.ui.deleteButton.setEnabled(True)

    def editPoint(self, row=None, col=None):
        if row is None:
            row = self.ui.pointsTable.currentRow()
        if row < 0:
            return
        dialog = OperatingPointDialog()
        dialog.setWindowTitle("Edit operating point {:d}".format(row+1))
        dialog.fromOperatingPoint(self.points.point(row))
        if dialog.exec():
            editedpoint = dialog.operatingPoint()
            items = self.itemsFromOperatingPoint(editedpoint) 
            for i in range(len(items)):
                self.ui.pointsTable.setItem(row, i, items[i])
            self.points.setPoint(row, deepcopy(editedpoint))

    def deletePoint(self):
        row = self.ui.pointsTable.currentRow()
        if row < 0:
            return
        self.ui.pointsTable.removeRow(row)
        self.points.deletePoint(row)
        if self.ui.pointsTable.rowCount() == 0:
            self.ui.editButton.setEnabled(False)
            self.ui.deleteButton.setEnabled(False)

    def setFlapHingePoint(self):
        dialog = FlapHingePointDialog()
        dialog.populate(self.points)
        if dialog.exec():
            self.points.setting("xflap").value = dialog.xflap()
            self.points.setting("yflap").value = dialog.yflap()
            self.points.setting("yflapSpecification").value = dialog.yflapSpecification()

    # Saves operating points
    def saveOperatingPoints(self):
        operatingpoints.setting("xflap").value = deepcopy(self.points.value("xflap"))
        operatingpoints.setting("yflap").value = deepcopy(self.points.value("yflap"))
        operatingpoints.setting("yflapSpecification").value = \
                        deepcopy(self.points.value("yflapSpecification"))
        operatingpoints.deleteAllPoints()
        for i in range(self.points.numPoints()):
            operatingpoints.addPoint(deepcopy(self.points.point(i)))
