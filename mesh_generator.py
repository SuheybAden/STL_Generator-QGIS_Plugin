from enum import Enum
import math
# from qgis.core import (
#     QgsMessageLog,
#     Qgis
# )

import numpy as np
import open3d as o3d
from osgeo import gdal, ogr
import pip._internal as pip


class EdgePoint(Enum):
    NONE = 0
    TOP_LEFT = 1
    TOP_RIGHT = 2
    BOTTOM_RIGHT = 3
    BOTTOM_LEFT = 4


class MeshGenerator:
    def __init__(self):
        pass

    def set_parameters(self, printHeight, baseHeight,
                       noDataValue, saveLocation,
                       bedX, bedY, lineWidth):
        # ***************************** USER INPUT *************************** #
        # Height of print excluding the base height (in mm)
        self.printHeight = printHeight
        # Height of extruded base (in mm)
        self.baseHeight = baseHeight
        self.noDataValue = noDataValue
        self.saveLocation = saveLocation

        # Printer settings in mm
        self.bedX = bedX
        self.bedY = bedY
        self.lineWidth = lineWidth

    def dem_to_mesh(self, source_dem):
        # try:
        #     pip.main(['install', 'open3d'])
        #     import open3d as o3d
        # except ImportError:
        #     print("Couldn't install open3d. Either restart the plugin or install open3d manually through the python console.")
        #     return
        input_array = self.generate_height_array(source_dem=source_dem)
        self.manually_generate_stl(input_array)

        # pcd = self.generate_point_cloud(array=input_array)
        # self.pcdToMesh(pcd=pcd)

    def generate_height_array(self, source_dem):
        dem = gdal.Open(source_dem, gdal.GA_ReadOnly)
        if not dem:
            # print("Failed to open DEM")
            # QgsMessageLog.logMessage("Failed to open DEM", level=Qgis.Critical)
            return

        band = dem.GetRasterBand(1)
        # noDataValue = band.GetNoDataValue()
        array = band.ReadAsArray()

        # ****************************** GET FINAL RESOLUTION OF IMAGE ***************************** #
        # Downscales array if the raster image is at a higher resolution than the printer can make
        imgWidth, imgHeight = array.shape

        # Gets the maximum resolution of the printer on each axis
        maxResX = self.bedX/self.lineWidth
        maxResY = self.bedY/self.lineWidth

        xScaling = math.floor(imgWidth/maxResX) if imgWidth > maxResX else 0
        yScaling = math.floor(imgHeight/maxResY) if imgHeight > maxResY else 0

        # Gets the larger of the two scaling factors
        scalingFactor = max(xScaling, yScaling)

        # # Debugging logs for checking scaling values
        # QgsMessageLog.logMessage(
        #     "X stats: " + str(imgWidth) + ", " + str(maxResX) + ", " + str(xScaling), level=Qgis.Info)
        # QgsMessageLog.logMessage(
        #     "Y stats: " + str(imgHeight) + ", " + str(maxResY) + ", " + str(yScaling), level=Qgis.Info)

        # Downscales array by scaling factor
        array = array[::scalingFactor, :: scalingFactor]

        # *************************** GET VERTICAL EXAGGERATION OF IMAGE *************************** #
        # Get min and max height values
        stats = band.GetStatistics(True, True)
        minValue = stats[0]
        maxValue = stats[1]

        imgWidth, imgHeight = array.shape
        heightDiff = maxValue - minValue

        self.verticalExaggeration = self.printHeight / heightDiff
        self.bottomLevel = (
            minValue * self.verticalExaggeration) - self.baseHeight

        np.save("C:/Code/array_data.npy", array)

        # # Debugging logs for checking scaling values
        # QgsMessageLog.logMessage(
        #     "X stats: " + str(imgWidth) + ", " + str(maxResX) + ", " + str(xScaling), level=Qgis.Info)
        # QgsMessageLog.logMessage(
        #     "Y stats: " + str(imgHeight) + ", " + str(maxResY) + ", " + str(yScaling), level=Qgis.Info)
        return array

    # Function for manually generating STL without the Open3D library
    def manually_generate_stl(self, array):
        with open(self.saveLocation + ".stl", "w+") as file:
            file.write("solid QGIS_STL\n")

        size_x, size_y = array.shape
        for x in range(size_x - 1):
            for y in range(size_y - 1):
                # Get a 2x2 window
                window = array[x:x+2, y:y+2]

                orientation = np.packbits(
                    (window != self.noDataValue).flatten())

                if (window[0][0] != self.noDataValue and
                        window[1][0] != self.noDataValue and
                        window[0][1] != self.noDataValue):

                    # Add top face
                    self.write_face([[x, y, window[0][0]*self.verticalExaggeration],
                                     [x, y + 1, window[0][1] *
                                         self.verticalExaggeration],
                                     [x + 1, y, window[1][0]*self.verticalExaggeration]])
                    # Add bottom face
                    self.write_face([[x, y, self.bottomLevel],
                                     [x + 1, y, self.bottomLevel],
                                     [x, y + 1, self.bottomLevel]])
                    # Add side faces
                    self.add_side_face(x, y, x + 1, y, array)
                    self.add_side_face(x, y, x, y + 1, array)
                    self.add_side_face(x + 1, y, x, y + 1, array)

                if (window[1][1] != self.noDataValue and
                        window[1][0] != self.noDataValue and
                        window[0][1] != self.noDataValue):
                    # Add top face
                    self.write_face([[x + 1, y + 1, window[1][1]*self.verticalExaggeration],
                                     [x + 1, y, window[1][0] *
                                         self.verticalExaggeration],
                                     [x, y + 1, window[0][1]*self.verticalExaggeration]])
                    # Add bottom face
                    self.write_face([[x + 1, y + 1, self.bottomLevel],
                                     [x, y + 1, self.bottomLevel],
                                     [x + 1, y, self.bottomLevel]])
                    # Add side faces
                    self.add_side_face(x + 1, y + 1, x + 1, y, array)
                    self.add_side_face(x + 1, y + 1, x, y + 1, array)
                    self.add_side_face(x + 1, y, x, y + 1, array)

        with open(self.saveLocation + ".stl", "a") as file:
            file.write("endsolid\n")

    def write_face(self, vertices):
        with open(self.saveLocation + ".stl", "a") as file:
            file.writelines(
                ["\tfacet normal 0.0 0.0 0.0\n", "\t\touter loop\n"])

            file.writelines(["\t\t\tvertex {0} {1} {2}\n".format(
                vertices[0][0], vertices[0][1], vertices[0][2]),
                "\t\t\tvertex {0} {1} {2}\n".format(
                vertices[1][0], vertices[1][1], vertices[1][2]),
                "\t\t\tvertex {0} {1} {2}\n".format(
                vertices[2][0], vertices[2][1], vertices[2][2])])

            file.writelines(["\t\tendloop\n", "\tendfacet\n"])

    def add_side_face(self, x1, y1, x2, y2, array):
        if(self.isEdgePoint(x1, y1, array) and self.isEdgePoint(x2, y2, array)):
            self.write_face([[x1, y1, array[x1][y1]*self.verticalExaggeration],
                             [x1, y1, self.bottomLevel],
                             [x2, y2, array[x2][y2]*self.verticalExaggeration]])
            self.write_face([[x1, y1, self.bottomLevel],
                             [x2, y2, self.bottomLevel],
                             [x2, y2, array[x2][y2]*self.verticalExaggeration]])

    def generate_point_cloud(self, array):
        # ***************************** GENERATE POINTCLOUD FROM IMAGE ARRAY ************************ #
        v = []
        n = []
        normal = 1
        x_size = array.shape[0]
        y_size = array.shape[1]

        # Debugging logs for checking mismatch in expected nodata value
        # QgsMessageLog.logMessage(
        #     str(noDataValue), level=Qgis.Info)
        # QgsMessageLog.logMessage(
        #     str(array[0][0]), level=Qgis.Info)

        for x in range(x_size):
            for y in range(y_size):
                if array[x][y] != self.noDataValue:
                    # Add the top facing points
                    # These are the ones that show the actual topography
                    point_height = array[x][y] * self.verticalExaggeration
                    v.append([x, y, point_height])
                    n.append([0, 0, normal])

                    # If this point is an edge, add points going down the side
                    if (self.isEdgePoint(x, y, array)):
                        self.addSidePoints(
                            x, y, v, n, edge_height=point_height)

                    # Add points to make a flat bottom
                    v.append([x, y, self.bottomLevel])
                    n.append([0, 0, -normal])

        vertices = np.array(v)
        normals = np.array(n)
        v = []

        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(vertices)
        pcd.normals = o3d.utility.Vector3dVector(normals)

        # pcd.normals = o3d.utility.Vector3dVector(np.zeros((1, 3)))
        # pcd.estimate_normals(fast_normal_computation=True)
        # pcd.orient_normals_consistent_tangent_plane(3)

        # STUFF FOR TRYING TO REMOVE OUTLIERS
        # voxel_down_pcd = pcd.voxel_down_sample(voxel_size=0.02)
        # cl, ind = voxel_down_pcd.remove_radius_outlier(nb_points=15, radius=3)

        # inlier_cloud = voxel_down_pcd.select_by_index(ind)
        # inlier_cloud.paint_uniform_color([0.8, 0.8, 0.8])

        # outlier_cloud = voxel_down_pcd.select_by_index(ind, invert=True)
        # outlier_cloud.paint_uniform_color([1.0, 0.0, 0.0])

        # print("Successfully generated point cloud")
        # QgsMessageLog.logMessage(
        #     "Successfully generated point cloud", level=Qgis.Info)

        # Display pointcloud
        o3d.visualization.draw_geometries([pcd])

        return pcd

    def pcdToMesh(self, pcd):
        # # Two ways of getting radius for ball pivoting reconstruction
        # distances = pcd.compute_nearest_neighbor_distance()
        # avg_dist = np.mean(distances)
        # radius = 4 * avg_dist

        # gt = dem.GetGeoTransform()
        # radius = 5.8 * max(gt[1], gt[5])

        # Ball Pivoting Algorithm
        # Need normals
        bpa_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
            pcd, o3d.utility.DoubleVector([.15, .5, 1, 1.5, 4, 10]))

        dec_bpa = bpa_mesh.simplify_quadric_decimation(100000)
        dec_bpa.remove_degenerate_triangles()
        dec_bpa.remove_duplicated_triangles()
        dec_bpa.remove_duplicated_vertices()
        dec_bpa.remove_non_manifold_edges()

        # Poisson Algorithm
        # poisson_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        #     pcd, depth=12, scale=2)[0]

        # bbox = pcd.get_axis_aligned_bounding_box()
        # p_mesh_crop = poisson_mesh.crop(bbox)

        # dec_poisson = poisson_mesh.simplify_quadric_decimation(100000)

        o3d.visualization.draw_geometries([dec_bpa])
        o3d.io.write_triangle_mesh(self.saveLocation + ".stl", dec_bpa)

    # Returns whether or not a data point is on the edge of the DEM or not

    def isEdgePoint(self, x, y, array):
        window = array[x-1:x+2, y-1:y+2]

        return window.size == 0 or self.noDataValue in window

    # Adds points to the vertices and normals to signify the side of the mesh extrusion

    def addSidePoints(self, x,  y, v, n, edge_height):
        for i in range(int(edge_height), int(self.bottomLevel), -2):
            v.append([x, y, i])
            n.append([1, 0, 0])


def main():
    mesh_generator = MeshGenerator()
    mesh_generator.set_parameters(printHeight=20,
                                  baseHeight=20,
                                  noDataValue=-9999,
                                  saveLocation="C:/Code/test",
                                  bedX=200,
                                  bedY=200,
                                  lineWidth=0.4)
    data = np.load("C:/Code/array_data.npy")
    test_array = np.array([[1, 2, 7, 21312, 590],
                           [3, 5, 9, 21093, -45],
                           [421, 214, -9999, 2913, 493],
                           [2891, 3902, 219, 4891, 214],
                           [324, 8421, 58, 32, 89412]])
    # x = 1
    # y = 0
    # print(test_array[x][y])
    # print(mesh_generator.isEdgePoint(x, y, test_array))
    mesh_generator.manually_generate_stl(data)


if __name__ == "__main__":
    main()
