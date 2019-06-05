import yaml
from Scientific.IO.FortranFormat import FortranFormat, FortranLine
from fortranformat import FortranRecordReader


def test_compare_fortran_format_readers():
    """
    Read a file line-by-line using the Scientific.IO and the fortranformat libraries
    and compare the elements in each line from each reader.  If any of the elements
    have differences, the test fails.
    :return: None
    """
    # The fortran format string
    fmtstr = 'i7,f9.3,1x,f8.2,1x,f8.2,1x,f8.2,f9.3,1x,f9.2,1x,f9.2,1x,f9.2,1x,f11.5,1x,i2,1x,i3,4x,i2,4x,i1,3x,i5,2x,a16,a12,4x,i1,2x,i1,3x,i1,1x,e13.6,1x,e13.6,1x,e13.6,1x,e13.6'

    # read the sample data
    data = yaml.load(open('test_resources/nrl_sample_input_data.yaml'))
    lines = data['lines']

    # define the parsers for each library
    fmt = FortranFormat(fmtstr)
    line_reader = FortranRecordReader(fmtstr)

    for n, line in enumerate(lines):
        # parse the line using Scientific.IO
        sio = FortranLine(line, fmt)

        # parse the line using fortran format
        ff = line_reader.read(line)

        # compare the values in each new list
        assert len(ff) == len(sio)
        for i in range(len(ff)):
            assert ff[i] == sio[i]
