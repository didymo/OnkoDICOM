import pydicom
from pydicom.dataelem import DataElement_from_raw

ds = pydicom.dcmread("../../dicom_sample/ct.0.dcm")

# Iterating through the entire Dataset (including Sequences)
# content = []
# for item in ds.keys():
#     print(item)
#
# for item in ds.iterall():
#     DataElement_from_raw(item)
#   print(item.name + "\t" + str(item.VM) + "\t" + item.VR + "\t" + str(item.tag) + "\t" + str(item.value))
#

import pydicom
from pydicom.data import get_testdata_files

print(__doc__)


def myprint(dataset, indent=0):
    """Go through all items in the dataset and print them with custom format

    Modelled after Dataset._pretty_str()
    """
    dont_print = ['Pixel Data', 'File Meta Information Version']

    indent_string = "   " * indent
    next_indent_string = "   " * (indent + 1)

    for data_element in dataset:
        if data_element.VR == "SQ":   # a sequence
            print(indent_string, data_element.name)
            for sequence_item in data_element.value:
                myprint(sequence_item, indent + 1)
                print(next_indent_string + "---------")
        else:
            if data_element.name in dont_print:
                print("""<item not printed -- in the "don't print" list>""")
            else:
                repr_value = repr(data_element.value)
                if len(repr_value) > 50:
                    repr_value = repr_value[:50] + "..."
                print("{0:s} {1:s} = {2:s}".format(indent_string,
                                                   data_element.name,
                                                   repr_value))


filename = get_testdata_files('MR_small.dcm')[0]
ds = pydicom.dcmread(filename)

myprint(ds)