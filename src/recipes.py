import constants
import market_data
import pickle
from os.path import exists
import UI


class Recipe:
    def __init__(self, recipe, common_name, ingrs, buy_price, sell_price, has_sub_recipe=False, sub_recipe=None):
        self.recipe = recipe
        self.common_name = common_name
        self.ingrs = ingrs
        self.has_sub_recipe = has_sub_recipe
        self.sub_recipe = sub_recipe
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.total_craft_price = 0
        self.should_be_crafted = False
        #self.craft_price = self.det_craft_price(self)

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

# TODO: Rework this so that it only happens once, and then we can use a library of the objects.

def create_recipe_dict():
    rec_dict = []
    file_exists = exists(constants.RECIPE_DICT)
    if not file_exists:
        with open(constants.MARKET_DATA_LOCAL, 'r') as recipe_file:
            recipe_file.readline()
            for line in recipe_file:
                print(line)
                name = line.split(",")[0]
                #print("** ", name)
                temp_name = UI.lookup_dump_data(name)
                #print("@* ", temp_name)
                recipe = pull_recipe(temp_name)
                rec_dict.append([name, recipe])
            print(rec_dict)
        with open(constants.RECIPE_DICT, 'wb') as recipe_dictionary:
            pickle.dump(rec_dict, recipe_dictionary)        
    else:
        with open(constants.RECIPE_DICT, 'rb') as file:
            rec_dict = pickle.load(file)
    print(rec_dict)      
    rec_dict = manip_dict(rec_dict)
    print_dict(rec_dict)
    return rec_dict

def manip_dict(rec_dict):
    i = 0
    for item in rec_dict:
        print("Manip_Dict: ", item[0])
        if item[1] is not None:
            #print("SETTING TO TRUE")
            rec_dict[i][1].is_craftable = True
            _, rec_dict = determine_craft_price(item[1], rec_dict)
        i += 1
    return rec_dict

def determine_craft_price(rec, rec_dict):
    for ingr in rec.ingrs:
        print("\tINGR: ", ingr.common_name)
        recipe = lookup_recipe(ingr.common_name, rec_dict)
        #print(ingr.common_name)
        if recipe:  
            print("\trecipe is craftable *************")   
            ingr.is_craftable = True       
            recipe.is_craftable = True
            #print(recipe.is_craftable)
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
    

def lookup_recipe(name, rec_dict):
    for item in rec_dict:
        if item[0] == name:
            if item[1] is not None:
                return item[1]

def print_dict(rec_dict):
    for item in rec_dict:
        print(item[0])
        
        if item[1] is not None:
            recipe = item[1]
            for ingredient in recipe.ingrs:
                print("\t" + ingredient.common_name)
                print(ingredient.is_craftable)
                if ingredient.is_craftable:
                    temp_recipe = lookup_recipe(ingredient.common_name, rec_dict)
                    print("\tCrafting Price: ", temp_recipe.total_craft_price)
                    if temp_recipe.should_be_crafted:
                        print("\tShould be crafted: ", True)
                        total_cost = float(temp_recipe.total_craft_price) * int(ingredient.qty)
                    else:
                        total_cost = float(temp_recipe.buy_price) * int(ingredient.qty)
                else:
                    total_cost = float(ingredient.buy_price    )
                print("\tQuantity: ", ingredient.qty)    
                print("\tCost: ", total_cost)
                
                


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
        i = 0
        while i < 10:
            if item == dict[i][0]:
                trans_item = dict[i][1]
                break
            i += 1
    else:
        for piece in dict:
            if item == piece[1]:
                trans_item = piece[0]
                break
    return trans_item

def eliminate_unused(rec, rec_dic):  # TODO: Rename this
        buy_item, name, buy_price, make_price = make_or_buy(rec)
        # TODO: left buy_price here because I might want to do something with it.  If not remove it later.
        total_cost = 0

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
                    if not buy_item:    # Crafting the item
                        this_price = make_price
                        i.buy_price = make_price
                    else:               # Buying the item
                        # this_price = buy_price
                        pass
                total_cost += float(i.buy_price) * int(i.qty)
            rec = rec.sub_recipe  

def pull_recipe(recipe_name):
    ingrlist = []
    qtylist = []
    try:
        file = open(constants.RECIPE_DUMP)

        lines = file.readlines()
        for line in lines:
            if line.split(",")[0] == recipe_name:
                #print("FOUND RECIPE: ", recipe_name)
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
                        return Recipe(recipe_name, cname, ingrlist, r_prices[0], r_prices[1], has_sub_recipe,
                                      sub_recipe)

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
