import constants
import market_data


class CookBook:
    def __init__(self, smelting, leatherworking, weaving, woodworking, stonecutting):
        self.smelting = smelting
        self.leatherworking = leatherworking
        self.weaving = weaving
        self.woodworking = woodworking
        self.stonecutting = stonecutting


class Recipe:
    def __init__(self, recipe, common_name, tradeskill, ingrs, buy_price, sell_price, has_sub_recipe=False,
                 sub_recipe=None):
        self.recipe = recipe
        self.common_name = common_name
        self.trade_skill = tradeskill
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


smelting_cookbook = {}
leatherworking_cookbook = {}
weaving_cookbook = {}
woodworking_cookbook = {}
stonecutting_cookbook = {}
unsorted_cookbook = []


def build_recipes():
    ingrlist = []
    qtylist = []
    try:
        file = open(constants.RECIPE_DUMP)
        lines = file.readlines()
        for line in lines:
            line_split = line.split(",")
            if line_split[2] == "RefinedResources" or line_split[2] == "CutStone":
                recipe_name = line.split(",")[0]
                trade_skill = line.split(",")[16]  # Trade skill associated with recipe

                # Check Ingredients required and add them to lists
                if bool(line_split[36]):  # Ingredient 1
                    ingrlist.append(line_split[36])
                    qtylist.append(line_split[50])
                if bool(line_split[38]):  # Ingredient 2
                    ingrlist.append(line_split[38])
                    qtylist.append(line_split[51])
                if bool(line_split[40]):  # Ingredient 3
                    ingrlist.append(line_split[40])
                    qtylist.append(line_split[52])
                if bool(line_split[42]):  # Ingredient 4
                    ingrlist.append(line_split[42])
                    qtylist.append(line_split[53])
                if bool(line_split[44]):  # Ingredient 5
                    ingrlist.append(line_split[44])
                    qtylist.append(line_split[54])
                if bool(line_split[46]):  # Ingredient 6
                    ingrlist.append(line_split[46])
                    qtylist.append(line_split[55])
                if bool(line_split[48]):  # Ingredient 7
                    ingrlist.append(line_split[48])
                    qtylist.append(line_split[56])

                for r in ingrlist:
                    cname = name_to_common(recipe_name)
                    r_prices = market_data.lookup_prices(cname)

                    _ingr_list = []
                    for _i, _j in zip(ingrlist, qtylist):
                        icname = name_to_common(_i)
                        if _i in constants.variable_ingrs:
                            cheapest = determine_cheapest(_i)
                            i_prices = market_data.lookup_prices(cheapest)
                        else:
                            i_prices = market_data.lookup_prices(icname)
                        _t = Ingredient(_i, icname, _j, i_prices[0], i_prices[1])  # Create ingredient object
                        _t.can_be_crafted = True
                        _ingr_list.append(_t)
                    # Create recipe object
                    finished_recipe = Recipe(recipe_name, cname, trade_skill, _ingr_list, r_prices[0], r_prices[1])
                    unsorted_cookbook.append(finished_recipe)

        file.close()
    except FileNotFoundError:
        print("File not found!")


def sort_recipes():
    for recipe in unsorted_cookbook:
        # TODO: POP them out
        tskill = recipe.trade_skill
        if tskill == "Smelting":
            smelting_cookbook[recipe.recipe] = recipe
            for x in recipe.ingrs:
                if x.ingredient in smelting_cookbook.keys():
                    recipe.sub_recipe = smelting_cookbook[x.ingredient]
                    print(x.common_name + " sorted")

        elif tskill == "Leatherworking":
            leatherworking_cookbook[recipe.recipe] = recipe
            for x in recipe.ingrs:
                if x.ingredient in leatherworking_cookbook.keys():
                    recipe.sub_recipe = leatherworking_cookbook[x.ingredient]

        elif tskill == "Weaving":
            weaving_cookbook[recipe.recipe] = recipe
            for x in recipe.ingrs:
                if x.ingredient in weaving_cookbook.keys():
                    recipe.sub_recipe = weaving_cookbook[x.ingredient]

        elif tskill == "Woodworking":
            woodworking_cookbook[recipe.recipe] = recipe
            for x in recipe.ingrs:
                if x.ingredient in woodworking_cookbook.keys():
                    recipe.sub_recipe = woodworking_cookbook[x.ingredient]

        elif tskill == "Stonecutting":
            stonecutting_cookbook[recipe.recipe] = recipe
            for x in recipe.ingrs:
                if x.ingredient in stonecutting_cookbook.keys():
                    recipe.sub_recipe = stonecutting_cookbook[x.ingredient]
        else:
            print(recipe.recipe + " was unsorted")


def build_cookbook():
    build_recipes()
    sort_recipes()
    master_cookbook = CookBook(smelting_cookbook, leatherworking_cookbook, weaving_cookbook,
                               woodworking_cookbook, stonecutting_cookbook)
    return master_cookbook

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
