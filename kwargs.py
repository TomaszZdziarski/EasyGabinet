"""keyword argument is all of the "unknown/unexpected" named argument that being passed by name.

for example, let's define a function with one argument"""

"""def func(a):
    print(a)"""
# now, if we call this function with an "unexpected" named argument like so

# func(b=3) # remember we didn't define b as an argument
#then we will get a TypeError. However, if we modify the function to accept these "unexpected" named arguments, then we can run the previous code

def func(a, **kwargs):
    print(a)
    print(kwargs["b"]) # now, if we pass an argument 'b' to the function, this will print its value (if we don't, we get a KeyError)

func(3, b=15)
