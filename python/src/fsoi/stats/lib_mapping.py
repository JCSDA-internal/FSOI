"""
lib_mapping.py contains mapping related functions:
"""
# pylint: disable=E0611,E0401
from mpl_toolkits.basemap import Basemap as _Basemap


class Projection(object):
    """
    Define a class for Projection
    """

    def __init__(self, projection='mill', resolution='c', cenlat=None, cenlon=None, stdlat1=None,
                 stdlat2=None, llcrnrlon=None, llcrnrlat=None, urcrnrlon=None, urcrnrlat=None,
                 boundinglat=None, width=None, height=None, mlabel_int=60.0, plabel_int=30.0,
                 meridians_labels=None, parallels_labels=None, **kwargs):
        """
        Initialize an class for Projection
        :param projection:
        :param resolution:
        :param cenlat:
        :param cenlon:
        :param stdlat1:
        :param stdlat2:
        :param llcrnrlon:
        :param llcrnrlat:
        :param urcrnrlon:
        :param urcrnrlat:
        :param boundinglat:
        :param width:
        :param height:
        :param mlabel_int:
        :param plabel_int:
        :param meridians_labels:
        :param parallels_labels:
        :param kwargs:
        """
        self.projection = projection
        self.resolution = resolution

        mlabel_int = int(mlabel_int)
        plabel_int = int(plabel_int)

        if self.projection == 'stere':
            print('%s projection has been implemented but not supported yet' % (self.projection))

        elif (self.projection in ['npstere', 'spstere']):
            self.meridians = range(-180, 180, mlabel_int)
            self.parallels = range(-90, 90, plabel_int)
            self.lon_0 = 0.0 if (cenlon is None) else cenlon
            self.meridians_labels = [0, 0, 1, 1] if (
                    meridians_labels is None) else meridians_labels
            if (self.projection == 'npstere'):
                self.boundinglat = 45.0 if (
                        boundinglat is None) else abs(boundinglat)
                self.parallels_labels = [1, 0, 0, 0] if (
                        parallels_labels is None) else parallels_labels
            if (self.projection == 'spstere'):
                self.boundinglat = - \
                    45.0 if (boundinglat is None) else -abs(boundinglat)
                self.parallels_labels = [0, 1, 0, 0] if (
                        parallels_labels is None) else parallels_labels

        elif (self.projection in ['mill', 'miller', 'merc', 'mercator']):
            self.llcrnrlon = 0.0 if (llcrnrlon is None) else llcrnrlon
            self.llcrnrlat = -90.0 if (llcrnrlat is None) else llcrnrlat
            self.urcrnrlon = 360.0 if (urcrnrlon is None) else urcrnrlon
            self.urcrnrlat = 90.0 if (urcrnrlat is None) else urcrnrlat
            self.meridians = range(-180, 180, mlabel_int)
            self.parallels = range(-90, 90, plabel_int)
            self.meridians_labels = [0, 0, 0, 1] if (
                    meridians_labels is None) else meridians_labels
            self.parallels_labels = [1, 0, 0, 0] if (
                    parallels_labels is None) else parallels_labels

        elif (self.projection in ['lcc', 'lambert']):
            self.cenlat = 0.0 if (cenlat is None) else cenlat
            self.cenlon = 0.0 if (cenlon is None) else cenlon
            self.stdlat1 = 0.0 if (stdlat1 is None) else stdlat1
            self.stdlat2 = 0.0 if (stdlat2 is None) else stdlat2
            self.width = 8.0 if (width is None) else width
            self.height = 11.0 if (height is None) else height
            self.meridians = range(-180, 180, mlabel_int)
            self.parallels = range(-90, 90, plabel_int)
            self.meridians_labels = [0, 0, 0, 1] if (
                    meridians_labels is None) else meridians_labels
            self.parallels_labels = [0, 1, 0, 0] if (
                    parallels_labels is None) else parallels_labels

        elif self.projection == 'ortho':
            print('projection "%s" has been implemented but not supported yet' % (self.projection))

        elif self.projection == 'robin':
            print('projection "%s" has been implemented but not supported yet' % (self.projection))

        else:
            msg = 'Error message from : setProj(projection)\n' + \
                  '   projection %s has not been implemented yet\n' % (self.projection) + \
                  '   valid options for projection are:\n' + \
                  '   "stere" | "npstere" | "spstere" | "mill" | "merc" | "lcc" | "ortho" | "robin"'
            print(msg)
            raise RuntimeError(msg)

        return


def createMap(proj, **kwargs):
    """
    Define a basemap object given the projection parameters from setProj
    Input  : Projection class
    Output : basemap object
    :param proj:
    :param kwargs:
    :return:
    """

    if proj.projection == 'stere':
        bmap = _Basemap(projection=proj.projection, **kwargs)

    elif (proj.projection in ['npstere', 'spstere']):
        bmap = _Basemap(projection=proj.projection,
                        resolution=proj.resolution,
                        lon_0=proj.cenlon,
                        boundinglat=proj.boundinglat,
                        **kwargs)

    elif (proj.projection in ['mill', 'miller', 'merc', 'mercator']):
        bmap = _Basemap(projection=proj.projection,
                        resolution=proj.resolution,
                        llcrnrlon=proj.llcrnrlon,
                        llcrnrlat=proj.llcrnrlat,
                        urcrnrlon=proj.urcrnrlon,
                        urcrnrlat=proj.urcrnrlat,
                        **kwargs)

    elif (proj.projection in ['lcc', 'lambert']):
        bmap = _Basemap(projection=proj.projection,
                        resolution=proj.resolution,
                        width=proj.width,
                        height=proj.height,
                        lat_0=proj.cenlat,
                        lon_0=proj.cenlon,
                        lat_1=proj.stdlat1,
                        lat_2=proj.stdlat2,
                        **kwargs)

    elif proj.projection == 'ortho':
        bmap = _Basemap(projection=proj.projection,
                        resolution=proj.resolution,
                        **kwargs)

    elif proj.projection == 'robin':
        bmap = _Basemap(projection=proj.projection,
                        resolution=proj.resolution,
                        **kwargs)

    else:
        msg = 'Error message from : createMap(proj)\n' + \
              '   projection %s has not been implemented yet\n' % (proj.projection) + \
              '   valid options for projection are:\n' + \
              '   "stere" | "npstere" | "spstere" | "mill" | "merc" | "lcc" | "ortho" | "robin"'
        print(msg)
        raise RuntimeError(msg)

    return bmap


def drawMap(bmap, proj, coastlines=True, fillcontinents=True, meridians=True, parallels=True,
            **kwargs):
    """
    Draw map with coastlines, fill continents, draw meridians and parallels, etc.
    :param bmap:
    :param proj:
    :param coastlines:
    :param fillcontinents:
    :param meridians:
    :param parallels:
    :param kwargs:
    :return:
    """
    if (coastlines):
        bmap.drawcoastlines(color='dimgray')
    if (fillcontinents):
        bmap.fillcontinents(color='lightgray', lake_color='white')
    if (meridians):
        bmap.drawmeridians(proj.meridians, labels=proj.meridians_labels)
    if (parallels):
        bmap.drawparallels(proj.parallels, labels=proj.parallels_labels)

    return
