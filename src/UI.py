import math
import signal
import sys
import time
import webbrowser

from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import QThread
from PyQt5.QtGui import QDoubleValidator, QStandardItemModel, QStandardItem, QFont, QIcon
from PyQt5.QtWidgets import QMenuBar, QAction, QMessageBox, QProgressBar

import constants
import recipes

import market_data


class Ui(QtWidgets.QWidget):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('../config/NW_TP3.ui', self)
        self.setWindowTitle("New World Trading Post")
        self.debug_tree = self.findChild(QtWidgets.QTreeView, "debugTreeView")
        self.menu_bar = QMenuBar(self)
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Recipe", "Qty", "Cost", "Total Qty", "Total Cost"])
        self.debug_tree.header().setDefaultSectionSize(410)
        self.debug_tree.setModel(self.model)
        self.debug_tree.setColumnWidth(0, 200)
        self.debug_tree.setColumnWidth(1, 50)
        self.debug_tree.setColumnWidth(2, 50)
        self.debug_tree.setColumnWidth(3, 60)
        self.debug_tree.setColumnWidth(4, 50)
        self.onlyDouble = QDoubleValidator(0.0, 500000.00, 2)
        self.capital = self.findChild(QtWidgets.QLineEdit, "Capital")
        # Validate capital input (min, max, decimal) Max not working as intended
        self.capital.setValidator(self.onlyDouble)
        self.capital.textEdited.connect(self.update)
        self.text_info = self.findChild(QtWidgets.QLabel, "text_info")
        self.text_info.setAlignment(QtCore.Qt.AlignCenter)
        self.skillCombo = self.findChild(QtWidgets.QComboBox, "skillCombo")
        self.skillCombo.currentTextChanged.connect(self.skill_combo_selected)
        self.buyCombo = self.findChild(QtWidgets.QComboBox, "buy_comboBox")
        self.buyCombo.currentTextChanged.connect(self.buy_combo_selected)
        self.sellCombo = self.findChild(QtWidgets.QComboBox, "sell_comboBox")
        self.sellCombo.currentTextChanged.connect(self.sell_combo_selected)
        self.buyQuantity = self.findChild(QtWidgets.QLineEdit, "buyQuantity")
        self.buyQuantity.setReadOnly(True)
        self.sellQuantity = self.findChild(QtWidgets.QLineEdit, "sellQuantity")
        self.sellQuantity.setReadOnly(True)
        self.buyIndividual = self.findChild(QtWidgets.QLineEdit, "buyIndividual")
        self.buyIndividual.setReadOnly(True)
        self.sellIndividual = self.findChild(QtWidgets.QLineEdit, "sellIndividual")
        self.sellIndividual.setReadOnly(True)
        self.buyFlip = self.findChild(QtWidgets.QLineEdit, "buyFlip")
        self.buyFlip.setReadOnly(True)
        self.sellFlip = self.findChild(QtWidgets.QLineEdit, "sellFlip")
        self.sellFlip.setReadOnly(True)

        self.master_cookbook = recipes.build_cookbook()  # Build all recipes and ingredients then store them
        self.parent_indexes = []
        self.can_make = 0
        self.total_ingr_cost = 0
        self.trade_skill = None
        #
        # End component initialization
        #
        self.show()
        self.create_menus()

    def create_menus(self):
        files_menu = self.menu_bar.addMenu("Files")
        reset_market = files_menu.addAction("Reset market data")
        reset_market.triggered.connect(self.fetch_market_action)

        help_menu = self.menu_bar.addMenu("Help")
        report_issue = help_menu.addAction("Report Issue")
        report_issue.triggered.connect(self.report_action)

        help_menu.addAction("Read me")

        about = help_menu.addAction("About")
        about.triggered.connect(self.about_action)

    def read_me_action(self):
        pass

    def about_action(self):
        about_dialog = QMessageBox()
        about_dialog.setWindowTitle("About this application")
        about_dialog.setText("THIS WAS FUCKING PAINFUL")
        about_dialog.exec()
        pass

    def report_action(self):
        webbrowser.open("https://github.com/rjbrown2/NWTP/issues/new")

    def fetch_market_action(self):
        market_data.fetch_market_data()

    def reset_sell(self):
        self.model.invisibleRootItem().removeRows(0, self.model.rowCount())  # Clear fields pertaining to sell drop down
        self.sellQuantity.setText("")
        self.sellIndividual.setText("")
        self.sellFlip.setText("")

    def reset_buy(self):
        self.buyQuantity.setText("")
        self.buyIndividual.setText("")
        self.buyFlip.setText("")

    def update(self):
        if self.capital.text() == "":
            self.reset_sell()
            self.reset_buy()
        if self.capital.text() != "" and float(self.capital.text()) > 500000.00:
            self.capital.setText(str(500000.00))
        if self.sellCombo.currentText() != "":
            self.sell_combo_selected()
        if self.buyCombo.currentText() != "":
            self.buy_combo_selected()

    def skill_combo_selected(self):
        self.sellCombo.clear()
        self.sellCombo.addItem("")
        skill_text = self.skillCombo.currentText()
        self.trade_skill = skill_text
        if skill_text == "Smelting":
            for recipe in self.master_cookbook.smelting.keys():
                temp = self.master_cookbook.smelting[recipe]
                self.sellCombo.addItem(temp.common_name)
        elif skill_text == "Leatherworking":
            for recipe in self.master_cookbook.leatherworking.keys():
                temp = self.master_cookbook.leatherworking[recipe]
                self.sellCombo.addItem(temp.common_name)
        elif skill_text == "Weaving":
            for recipe in self.master_cookbook.weaving.keys():
                temp = self.master_cookbook.weaving[recipe]
                self.sellCombo.addItem(temp.common_name)
        elif skill_text == "Woodworking":
            for recipe in self.master_cookbook.woodworking.keys():
                temp = self.master_cookbook.woodworking[recipe]
                self.sellCombo.addItem(temp.common_name)
        elif skill_text == "Stonecutting":
            for recipe in self.master_cookbook.stonecutting.keys():
                temp = self.master_cookbook.stonecutting[recipe]
                self.sellCombo.addItem(temp.common_name)

    def sell_combo_selected(self):
        if self.capital.text == "":
            self.reset_sell()
            return

        item = self.sellCombo.currentText()
        if self.sellCombo.textActivated:
            if item != "":
                self.populate_treeview(item)
        if not item:
            self.reset_sell()
            return

    def fill_tree_values(self):
        index = self.parent_indexes
        some_name = "Linen"
        mult_quantity = False
        mult_amount = 0
        k = 0
        for i in index:
            if isinstance(i, list):
                for j in i:
                    if isinstance(j, list):
                        if self.model.itemFromIndex(j[0]).text() == some_name:
                            mult_amount = int(self.model.itemFromIndex(j[1]).text())
                        qty = self.model.itemFromIndex(j[1])
                        price = self.model.itemFromIndex(j[2])
                        t_qty = self.model.itemFromIndex(j[3])
                        t_cost = self.model.itemFromIndex(j[4])
                        if mult_quantity:
                            temp_qty = int(float(qty.text())) * mult_amount
                            temp_cost = float(price.text()) * mult_amount
                        else:
                            temp_qty = int(float(qty.text()))
                            temp_cost = float(price.text())
                        total_quantity = temp_qty * self.can_make  # Total qty = qty * can make
                        total_cost = self.can_make * temp_cost  # Total cost = total qty * cost
                        self.model.setData(t_qty.index(), total_quantity)
                        self.model.setData(t_cost.index(), total_cost)
            else:
                if self.model.item(k, 0).text() == some_name:
                    mult_quantity = True
                k += 1

    def populate_treeview(self, data_in):
        self.model.setRowCount(0)
        self.total_ingr_cost = 0
        key = lookup_dump_data(data_in)
        if self.trade_skill == "Smelting":
            current_book = self.master_cookbook.smelting
        elif self.trade_skill == "Leatherworking":
            current_book = self.master_cookbook.leatherworking
        elif self.trade_skill == "Weaving":
            current_book = self.master_cookbook.weaving
        elif self.trade_skill == "Woodworking":
            current_book = self.master_cookbook.woodworking
        elif self.trade_skill == "Stonecutting":
            current_book = self.master_cookbook.stonecutting
        else:
            return

        recipe = current_book[key]
        self.parent_indexes = []  # Parent index list
        loop_trigger = True
        children = []  # Children index list
        while loop_trigger:
            children = []
            loop_trigger = recipe.has_sub_recipe
            parent_font = QFont("Segoe UI", 9, QFont.Bold)
            parent = QStandardItem(recipe.common_name)  # Parent Creation
            parent.setFont(parent_font)
            if not recipe.should_be_crafted:
                parent.setIcon(QIcon("../resources/NW-coins-96x.ico"))
            self.parent_indexes.append(parent.index())
            parent.setEditable(False)
            recipe_string = QStandardItem(str(recipe.buy_price))
            recipe_string.setFont(parent_font)
            self.model.appendRow([parent, QStandardItem(""), recipe_string])
            ingr_list = recipe.ingrs

            for _i in ingr_list:
                ingr = QStandardItem(_i.common_name)
                qty = QStandardItem(_i.qty)

                cost = float(_i.buy_price) * int(_i.qty)  # Cost = Buy Price * Qty
                self.total_ingr_cost += cost  # total_ingr_cost = cost of all ingredients not accounting for conversions

                buy_price = QStandardItem(str("{:.2f}".format(cost)))
                buy_price.setEditable(False)

                total_qty = QStandardItem(str(0))
                total_qty.setEditable(False)

                total_cost = QStandardItem(str(0))
                total_cost.setEditable(False)

                parent.appendRow([ingr, qty, buy_price, total_qty, total_cost])  # Child Creation
                children.append([ingr.index(), qty.index(), buy_price.index(), total_qty.index(), total_cost.index()])

            recipe = recipe.sub_recipe
            self.parent_indexes.append(children)  # Append children to parent index
        self.debug_tree.expandAll()
        text = "<p><b>Note:</b> The <img src=\"../resources/NW-coins-96x.ico\" width=\"16\" " \
               "height=\"16\">&nbsp;&nbsp;icon means you should purchase these items for the most profit! "
        self.text_info.setText(text)
        self.do_math(current_book)  # Do fucking math

    def buy_combo_selected(self):
        item = self.buyCombo.currentText()
        if self.capital.text() == "" or not item:
            self.reset_buy()
            return

        capital = float(self.capital.text())
        can_buy, buy_individual, buy_flip = 0.0, 0.0, 0.0

        p = market_data.lookup_prices(item)
        buy_price, sell_price = p[0], p[1]

        can_buy = math.floor(capital / buy_price)  # Can buy = floor(Capital / buy price)
        buy_individual = sell_price * can_buy  # Buy individual = sell price * can_buy
        buy_profit = buy_individual - capital  # Buy Profit = Buy individual - capital
        self.buyQuantity.setText(str(can_buy))
        self.buyIndividual.setText(str("{:.2f}".format(buy_individual)))

        if buy_profit < 0:
            self.buyFlip.setStyleSheet("color: red;")
        else:
            self.buyFlip.setStyleSheet("color: green;")

        self.buyFlip.setText(str("{:.2f}".format(buy_profit)))

    # TODO: Finish this, might still have issues in recipe file
    def total_cost(self, recipe):
        for ingredient in recipe.ingrs:
            pass

    def do_math(self, current_cookbook):
        # TODO:  Verify formulas for sell boxes
        if self.capital.text() == "":
            self.reset_buy()
            self.reset_sell()
            return

        capital = float(self.capital.text())

        item = self.sellCombo.currentText()
        print(current_cookbook)
        #self.total_cost(recipes.lookup_recipe(item, current_cookbook))
        print("MATH: COST: ", self.total_ingr_cost)
        # recipe = recipes.lookup_recipe(item)

        # for ingredient in recipe:
        #     ingredient_cost = ingredient.buy_price
        #     if ingredient.is_craftable:
        #         if ingredient.buy_price > ingredient.total_craft_price:
        #             ingredient_cost = ingredient.total_craft_price
        #     total_cost += ingredient_cost
        p = market_data.lookup_prices(item)

        sell_individual = self.can_make * float(p[1])  # Formulate and set sell individual
        self.sellIndividual.setText(str("{:.2f}".format(sell_individual)))

        sell_flip = sell_individual - capital  # Formulate and set sell flip
        f_sell_flip = "{:.2f}".format(sell_flip)
        if sell_flip < 0:
            self.sellFlip.setStyleSheet("color: red;")
        else:
            self.sellFlip.setStyleSheet("color: green;")
        self.sellFlip.setText(f_sell_flip)
        self.fill_tree_values()

    def eliminate_unused(self, rec):  # TODO: Rename this
        buy_item, name, buy_price, make_price = make_or_buy(rec)
        # TODO: left buy_price here because I might want to do something with it.  If not remove it later.
        total_cost = 0
        if buy_item:  # If we're buying the item, use that price in calculations
            text = "You should <b><u><font color = \"Red\">BUY</font></u></b> the <u><b>" + \
                   name + "</b></u> from the <i>Selling</i> box for maximum profit."
        else:  # Crafting the item
            text = "You should <b><u><font color = \"Red\">CRAFT</font></u></b> the <u><b>" + \
                   name + "</b></u> from the <i>Selling</i> box for the maximum profit."

        self.text_info.setText(text)
        loop_val = True
        while loop_val:
            if rec.has_sub_recipe:
                if rec.sub_recipe.common_name == name:
                    loop_val = False
            else:
                loop_val = False
            for i in rec.ingrs:
                this_price = i.buy_price
                if i.common_name == name:
                    if not buy_item:  # Crafting the item
                        this_price = make_price
                        i.buy_price = make_price
                    else:  # Buying the item
                        # this_price = buy_price
                        pass
                total_cost += float(i.buy_price) * int(i.qty)
            rec = rec.sub_recipe
        if self.capital.text() == "":
            self.reset_sell()
            return
        can_make = math.floor(float(self.capital.text()) / total_cost)
        self.sellQuantity.setText(str(can_make))
        self.can_make = can_make


class ProgressDialog(QThread):
    # progress_update = QtCore.Signal(int)

    def __init__(self):
        QThread.__init__(self)
        dialog = QMessageBox(QMessageBox.NoIcon, "TITLE", "TEXT", QMessageBox.NoButton)
        layout = dialog.layout()
        layout.itemAtPosition(layout.rowCount() - 1, 0).widget().hide()

        progress_bar = QProgressBar()
        layout.addWidget(progress_bar, layout.rowCount(), 0, 1, layout.columnCount(), QtCore.Qt.AlignCenter)

        dialog.show()

    def __del__(self):
        self.wait()

    def run(self):
        #  LOGIC
        while 1:
            max_value = 1
            self.progress_update.emit(max_value)
            time.sleep(1)

    def updateProgressBar(self, max_value):
        self.ProgressDialog.progress_bar.setValue(100)


def make_or_buy(rec):
    buy_item = False
    make_price, buy_price, common_name = lowest_parent_recipe(rec)
    if make_price > buy_price:
        buy_item = True
    return buy_item, common_name, buy_price, make_price


def lowest_parent_recipe(rec):
    while rec.has_sub_recipe:
        rec = rec.sub_recipe
    cost_of_one = int(rec.ingrs[0].qty) * float(rec.ingrs[0].buy_price)
    rec_buy_price = rec.buy_price
    return cost_of_one, rec_buy_price, rec.common_name


def lookup_dump_data(item, reverse_lookup=False):
    dict = constants.dict
    trans_item = item
    if reverse_lookup:
        for piece in dict:
            if item == piece[0]:
                trans_item = piece[1]
                break
    else:
        for piece in dict:
            if item == piece[1]:
                trans_item = piece[0]
                break
    return trans_item


if __name__ == "__main__":
    market_data.fetch_market_data()  # Fetch Market Data from google sheets
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    dict = constants.dict

    app = QtWidgets.QApplication(sys.argv)

    # pd = ProgressDialog()
    window = Ui()
    window.show()
    app.exec_()
