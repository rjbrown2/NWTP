import constants


class Recipe:
    def __init__(self, recipe, ingrs, qtys, has_sub_recipe=False, sub_recipe=None):
        self.recipe = recipe
        self.ingrs = ingrs
        self.qtys = qtys
        self.has_sub_recipe = has_sub_recipe
        self.sub_recipe = sub_recipe


def pull_recipe(recipe_name):
    ingrlist = []
    qtylist = []
    recipe_found = False

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

                # recursively check for sub recipes
                for r in ingrlist:
                    sub_rec = pull_recipe(r)
                    if sub_rec is not None:
                        # Found a sub recipe
                        has_sub_recipe = True
                        sub_recipe = sub_rec
                        return Recipe(recipe_name, ingrlist, qtylist, has_sub_recipe, sub_recipe)

                return Recipe(recipe_name, ingrlist, qtylist)

            if recipe_found:
                break

        if not recipe_found:
            return None

        file.close()
    except FileNotFoundError:
        print("File not found!")

    input("PRESS")


def print_results(recipe):
    output_string = ""
    result = pull_recipe(recipe)
    while recipe.has_sub_recipe:
        output_string += recipe.recipe + " requires: \n"
        for i, j in zip(recipe.ingrs, recipe.qtys):
            output_string += (i + " " + j + "\n")
        output_string += "\n"
        recipe = recipe.sub_recipe
    output_string += recipe.recipe + "requires: \n"
    for i, j in zip(recipe.ingrs, recipe.qtys):
        output_string += (i + " " + j + "\n")

# def main():
#     recipe = pull_recipe("IngotT4")

#     # This recursion works yo
#     while recipe.has_sub_recipe:
#         print(recipe.recipe + " requires:")
#         for i, j in zip(recipe.ingrs, recipe.qtys):
#             print(i + " " + j)
#         print("\n")
#         recipe = recipe.sub_recipe
#     print(recipe.recipe + " requires:")
#     for i, j in zip(recipe.ingrs, recipe.qtys):
#         print(i + " " + j)


# if __name__ == "__main__":
#     main()
