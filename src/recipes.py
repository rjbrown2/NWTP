import constants
import market_data


class Recipe:
    def __init__(self, recipe, common_name, ingrs, buy_price, sell_price, has_sub_recipe=False, sub_recipe=None):
        self.recipe = recipe
        self.common_name = common_name
        self.ingrs = ingrs
        self.has_sub_recipe = has_sub_recipe
        self.sub_recipe = sub_recipe
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.craft_price = self.determine_craft_price()
    
    def determine_craft_price(self):
        craft_price = 0
        for ingredient in self.ingrs:            
            craft_price += (float(ingredient.buy_price) * int(ingredient.qty))
        return craft_price

class Ingredient:
    def __init__(self, ingredient, common_name, qty, buy_price, sell_price, parent_recipe=None):
        self.ingredient = ingredient
        self.common_name = common_name
        self.qty = qty
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.parent_recipe = parent_recipe
        self.craft_price = 0.0
        self.can_be_crafted = False     

def pull_recipe(recipe_name):
    ingrlist = []
    qtylist = []
    try:
        file = open(constants.RECIPE_DUMP)

        lines = file.readlines()
        for line in lines:
            if line.split(",")[0] == recipe_name:
                # Recipe Found
                # Check Ingredients required and add them to lists
                if bool(line.split(",")[36]):  # Ingredient 1
                    ingrlist.append(line.split(",")[36])
                    qtylist.append(line.split(",")[50])
                if bool(line.split(",")[38]):  # Ingredient 2
                    ingrlist.append(line.split(",")[38])
                    qtylist.append(line.split(",")[51])
                if bool(line.split(",")[40]):  # Ingredient 3
                    ingrlist.append(line.split(",")[40])
                    qtylist.append(line.split(",")[52])
                if bool(line.split(",")[42]):  # Ingredient 4
                    ingrlist.append(line.split(",")[42])
                    qtylist.append(line.split(",")[53])
                if bool(line.split(",")[44]):  # Ingredient 5
                    ingrlist.append(line.split(",")[44])
                    qtylist.append(line.split(",")[54])
                if bool(line.split(",")[46]):  # Ingredient 6
                    ingrlist.append(line.split(",")[46])
                    qtylist.append(line.split(",")[55])
                if bool(line.split(",")[48]):  # Ingredient 7
                    ingrlist.append(line.split(",")[48])
                    qtylist.append(line.split(",")[56])

                # Recursively check for recipes
                for r in ingrlist:
                    sub_rec = pull_recipe(r)
                    if sub_rec is not None:
                        # Found a sub recipe
                        has_sub_recipe = True
                        sub_recipe = sub_rec
                        cname = name_to_common(recipe_name)
                        r_prices = market_data.lookup_prices(cname)

                        _t_list = []
                        for _i, _j in zip(ingrlist, qtylist):
                            icname = name_to_common(_i)
                            i_prices = market_data.lookup_prices(icname)
                            _t = Ingredient(_i, icname, _j, i_prices[0], i_prices[1])  # Create recipe object
                            _t.can_be_crafted = True
                            _t_list.append(_t)
                        ingrlist = _t_list
                        return Recipe(recipe_name, cname, ingrlist, r_prices[0], r_prices[1], has_sub_recipe, sub_recipe)

                _t_list = []
                for _i, _j in zip(ingrlist, qtylist):
                    if _i in constants.variable_ingrs:
                        cheapest = determine_cheapest(_i)
                        i_prices = market_data.lookup_prices(cheapest)
                        _t = Ingredient(_i, cheapest, _j, i_prices[0], i_prices[1])  # Converted item to cheapest item
                        _t_list.append(_t)
                    else:
                        icname = name_to_common(_i)
                        i_prices = market_data.lookup_prices(icname)
                        _t = Ingredient(_i, icname, _j, i_prices[0], i_prices[1])  # Else item is fine, no sub rec
                        _t.can_be_crafted = False
                        _t_list.append(_t)

                ingrlist = _t_list
                cname = name_to_common(recipe_name)
                r_prices = market_data.lookup_prices(cname)
                return Recipe(recipe_name, cname, ingrlist, r_prices[0], r_prices[1])

        file.close()
    except FileNotFoundError:
        print("File not found!")


# TODO: Add a way to determine the cheapest of "hide"
# TODO: Add a way to determine the cheapest of "fiber"
def determine_cheapest(item):
    with open(constants.MARKET_DATA_LOCAL, "r") as read_file:
        lines = read_file.readlines()
        result = [L for L in lines if item.upper() in L.upper()]
        result += [L for L in lines if "TIMBER" in L.upper()]  # Oddball woods
        result += [L for L in lines if "LUMBER" in L.upper()]

        price_list = []
        for x in result:
            price_list.append(x.split(",")[1])

        cheapest_price = min(price_list)
        min_index = price_list.index(cheapest_price)
        cheapest = result[min_index].split(",")[0]
        return cheapest


def name_to_common(item):
    dict = constants.dict
    trans_item = item
    for piece in dict:
        if item == piece[0]:
            trans_item = piece[1]
            break
        # else: print("NOTHING FOUND")
    return trans_item
