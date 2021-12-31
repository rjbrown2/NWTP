import pickle
from os.path import exists

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
        self.total_craft_price = 0
        self.should_be_crafted = False


class Ingredient:
    def __init__(self, ingredient, common_name, qty, buy_price, sell_price, parent_recipe=None):
        self.ingredient = ingredient
        self.common_name = common_name
        self.qty = qty
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.parent_recipe = parent_recipe
        self.is_craftable = False
        self.can_be_crafted = False


smelting_cookbook = {}
leatherworking_cookbook = {}
weaving_cookbook = {}
woodworking_cookbook = {}
stonecutting_cookbook = {}
unsorted_cookbook = []


def build_recipes():
    try:
        file = open(constants.RECIPE_DUMP)
        lines = file.readlines()
        for line in lines:
            ingrlist = []
            qtylist = []
            line_split = line.split(",")
            if line_split[0] in constants.IGNORED_RECIPES:
                continue
            if line_split[2] == "RefinedResources" or line_split[2] == "CutStone":
                recipe_name = line_split[0]
                trade_skill = line_split[16]  # Trade skill associated with recipe

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
                    _ingr_list.append(_t)
                # Create recipe object
                finished_recipe = Recipe(recipe_name, cname, trade_skill, _ingr_list, r_prices[0], r_prices[1])
                unsorted_cookbook.append(finished_recipe)

        file.close()
    except FileNotFoundError:
        print("File not found!")


def sort_recipes():
    print("Sorting recipes...")
    while len(unsorted_cookbook) > 0:
        for recipe in unsorted_cookbook:
            tskill = recipe.trade_skill
            index = unsorted_cookbook.index(recipe)
            if tskill == "Smelting":
                smelting_cookbook[recipe.recipe] = recipe
                unsorted_cookbook.pop(index)

            elif tskill == "Leatherworking":
                leatherworking_cookbook[recipe.recipe] = recipe
                unsorted_cookbook.pop(index)

            elif tskill == "Weaving":
                weaving_cookbook[recipe.recipe] = recipe
                unsorted_cookbook.pop(index)

            elif tskill == "Woodworking":
                woodworking_cookbook[recipe.recipe] = recipe
                unsorted_cookbook.pop(index)

            elif tskill == "Stonecutting":
                stonecutting_cookbook[recipe.recipe] = recipe
                unsorted_cookbook.pop(index)
            else:
                print(recipe.recipe + " was unsorted")

    print("Setting sub recipes...")
    # TODO: Add flags to say ingredient is craftable
    for recipe in smelting_cookbook.values():
        for x in recipe.ingrs:
            if x.ingredient != "CharcoalT1" and x.ingredient in smelting_cookbook.keys():
                x.is_craftable = True
                recipe.has_sub_recipe = True
                recipe.sub_recipe = smelting_cookbook[x.ingredient]
                break

    for recipe in leatherworking_cookbook.values():
        for x in recipe.ingrs:
            if x.ingredient in leatherworking_cookbook.keys():
                x.is_craftable = True
                recipe.has_sub_recipe = True
                recipe.sub_recipe = leatherworking_cookbook[x.ingredient]
                break

    for recipe in weaving_cookbook.values():
        for x in recipe.ingrs:
            if x.ingredient in weaving_cookbook.keys():
                x.is_craftable = True
                recipe.has_sub_recipe = True
                recipe.sub_recipe = weaving_cookbook[x.ingredient]
                break

    for recipe in woodworking_cookbook.values():
        for x in recipe.ingrs:
            if x.ingredient in woodworking_cookbook.keys():
                x.is_craftable = True
                recipe.has_sub_recipe = True
                recipe.sub_recipe = woodworking_cookbook[x.ingredient]
                break

    for recipe in stonecutting_cookbook.values():
        for x in recipe.ingrs:
            if x.ingredient in stonecutting_cookbook.keys():
                x.is_craftable = True
                recipe.has_sub_recipe = True
                recipe.sub_recipe = stonecutting_cookbook[x.ingredient]
                break


def build_cookbook():
    file_exists = exists(constants.RECIPE_DICT)
    if not file_exists:
        build_recipes()
        sort_recipes()
        master_cookbook = CookBook(smelting_cookbook, leatherworking_cookbook, weaving_cookbook,
                                   woodworking_cookbook, stonecutting_cookbook)
        with open(constants.RECIPE_DICT, "wb") as recipe_dictionary:
            pickle.dump(master_cookbook, recipe_dictionary)
    else:
        with open(constants.RECIPE_DICT, "rb") as file:
            master_cookbook = pickle.load(file)

    master_cookbook = modify_cookbooks(master_cookbook)
    print(master_cookbook)
    return master_cookbook


def modify_cookbooks(master_cookbook):
    # smelting_cookbook = {}
    # leatherworking_cookbook = {}
    # weaving_cookbook = {}
    # woodworking_cookbook = {}
    # stonecutting_cookbook = {}
    temp_list = [master_cookbook.smelting, master_cookbook.leatherworking, master_cookbook.weaving,
                 master_cookbook.woodworking, master_cookbook.stonecutting]
    return_list = []
    for cookbook in temp_list:
        for recipe in cookbook.values():
            _, mod_dict = determine_craft_price(recipe, cookbook)
        return_list.append(mod_dict)
    mod_book = CookBook(return_list[0], return_list[1], return_list[2], return_list[3], return_list[4])
    return mod_book

    # TODO: Add a way to determine the cheapest of "hide"
    # TODO: Add a way to determine the cheapest of "fiber"


def determine_craft_price(rec, rec_dict):
    # rec_dict should be a master_cookbook.{cookbook}
    for ingr in rec.ingrs:
        print("\tINGR: ", ingr.common_name)
        recipe = lookup_recipe(ingr.common_name, rec_dict)
        # print(ingr.common_name)
        if recipe:
            print("\trecipe is craftable *************")
            ingr.is_craftable = True
            recipe.is_craftable = True
            # print(recipe.is_craftable)
            if recipe.should_be_crafted:
                rec.sub_recipe.should_be_crafted = True
                ingr.should_be_crafted = True
            if recipe.total_craft_price != 0:
                print("\t\t@@@ Using Current price for: ", recipe.common_name)
                price, _ = determine_craft_price(recipe, rec_dict)
                rec.total_craft_price += recipe.total_craft_price
            else:
                print("\t\t@@@ Looking up recipe: ", recipe.common_name)
                price, rec_dict = determine_craft_price(recipe, rec_dict)
                recipe.total_craft_price += float(price)
        else:
            rec.total_craft_price += float(ingr.buy_price) * int(ingr.qty)
    if rec.total_craft_price < rec.buy_price:
        rec.should_be_crafted = True
    return rec.total_craft_price, rec_dict


def lookup_recipe(rec_name, cookbook):
    # cookbook should be a master_cookbook.{cookbook}
    for recipe in cookbook.keys():
        if recipe == rec_name:
            return cookbook[rec_name]


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


def name_to_common(item, reverse=False):
    dict = constants.dict
    trans_item = item
    for piece in dict:
        if reverse:
            if item == piece[1]:
                trans_item == piece[0]
                break
        else:
            if item == piece[0]:
                trans_item = piece[1]
                break
        # else: print("NOTHING FOUND")
    return trans_item
