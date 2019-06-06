import ucar.ma2.ArrayFloat;
import ucar.nc2.Dimension;
import ucar.nc2.Variable;
import ucar.nc2.dataset.NetcdfDataset;

import java.util.ArrayList;
import java.util.List;

public class TestNetCDF
{
    public static void main(String[] args) throws Throwable
    {
        /* open the data file */
        String file = "/tmp/sample.nc";
        NetcdfDataset data = NetcdfDataset.openDataset(file);

        /* make list of variables to read */
        Variable kx = data.findVariable("kx");
        List<Variable> variableList = new ArrayList<>();
        variableList.add(kx);

        /* read the data */
        ArrayFloat.D2 kxData = (ArrayFloat.D2) data.readArrays(variableList).get(0);

        /* print the data */
        List<Dimension> dimensions = kx.getDimensions();
        int I = dimensions.get(0).getLength();
        int J = dimensions.get(1).getLength();
        for(int i = 0; i < I; i++)
        {
            for (int j = 0; j < J; j++)
                System.out.print(kxData.get(i, j) + ", ");
            System.out.println();
        }
    }
}
