"""Some helper functions used across scripts"""

def sort_mixed_list(mixed_list: list) -> list:
    '''Helper function for sorting mixed number and letter lists'''
    # Define a custom key function
    def sort_key(element):
        # Check if the element can be converted to an integer
        if element.isdigit():
            # Return a tuple with 0 (indicating it's an integer) and its numeric value
            return (0, int(element))
        else:
            # Return a tuple with 1 (indicating it's a string) and the string itself
            return (1, element)

    # Sort the list using the custom key function
    sorted_list = sorted(mixed_list, key=sort_key)
    return sorted_list
