import numpy as np
from osgeo import gdal, ogr
import pip._internal as pip

verticalExaggeration = .01
noDataValue = -9999
bottomLevel = -25.0


def dem_to_mesh(source_dem):
    try:
        pip.main(['install', 'open3d'])
        import open3d as o3d
    except ImportError:
        print("Couldn't install open3d. Either restart the plugin or install open3d manually through the python console.")
        return

    dem = gdal.Open(source_dem, gdal.GA_ReadOnly)
    if not dem:
        print("Failed to open DEM")
        return

    # gt = dem.GetGeoTransform()
    # radius = 5.8 * max(gt[1], gt[5])

    band = dem.GetRasterBand(1)
    array = band.ReadAsArray()
    print(array.shape)

    v = []
    n = []
    normal = 1
    x_size = array.shape[0]
    y_size = array.shape[1]
    print(array[10][10])
    for x in range(x_size):
        for y in range(y_size):
            if array[x][y] != noDataValue:
                # Add the top facing points
                # These are the ones that show the actual topography
                point_height = array[x][y] * verticalExaggeration
                v.append([x, y, point_height])
                n.append([0, 0, normal])

                # faces = []
                # # Add face to the left of the current point
                # if (x > 0 and y < y_size - 1 and array[x-1][y] != noDataValue
                #         and array[x-1][y+1] != noDataValue):
                #     face.append([[x, y, array[x, y]],
                #                  [x-1, y, array[x-1, y]],
                #                  [x-1, y+1, array[x-1, y+1]]])

                # # Add face to the bottom-left of the current point
                # if (x > 0 and y < y_size - 1 and array[x][y+1] != noDataValue
                #         and array[x-1][y+1] != noDataValue):
                #     face.append([[x, y, array[x, y]],
                #                  [x, y+1, array[x, y+1]],
                #                  [x-1, y+1, array[x-1, y+1]]])

                # # Add face to the bottom-right of the current point
                # if (x < x_size - 1 and y < y_size - 1
                #     and array[x+1][y+1] != noDataValue
                #         and array[x][y+1] != noDataValue):
                #     face.append([[x, y, array[x, y]],
                #                  [x+1, y+1, array[x+1, y+1]],
                #                  [x, y+1, array[x, y+1]]])

                # # Add face to the right of the current point
                # if (x < x_size - 1 and y < y_size - 1
                #     and array[x+1][y+1] != noDataValue
                #         and array[x+1][y] != noDataValue):
                #     face.append([[x, y, array[x, y]],
                #                  [x+1, y+1, array[x+1, y+1]],
                #                  [x+1, y, array[x+1, y]]])

                # If this point is an edge, add points going down the side
                if (isEdgePoint(x, y, array)):
                    addSidePoints(
                        x, y, v, n, edge_height=point_height)

                # Add points to make a flat bottom
                v.append([x, y, bottomLevel])
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

    print("Successfully generated point cloud")

    # distances = pcd.compute_nearest_neighbor_distance()
    # avg_dist = np.mean(distances)
    # radius = 4 * avg_dist

    # # Need normals
    # bpa_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
    # 	pcd, o3d.utility.DoubleVector([.15, .5, 1, 1.5, 4, 10]))

    # # dec_bpa = bpa_mesh.simplify_quadric_decimation(100000)
    # # dec_bpa.remove_degenerate_triangles()
    # # dec_bpa.remove_duplicated_triangles()
    # # dec_bpa.remove_duplicated_vertices()
    # # dec_bpa.remove_non_manifold_edges()

    # # poisson_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
    # #     pcd, depth=12, scale=2)[0]

    # # bbox = pcd.get_axis_aligned_bounding_box()
    # # p_mesh_crop = poisson_mesh.crop(bbox)

    # # dec_poisson = poisson_mesh.simplify_quadric_decimation(100000)

    # o3d.visualization.draw_geometries([bpa_mesh])
    # o3d.io.write_triangle_mesh("bpa_mesh.obj", bpa_mesh)

# Returns whether or not a data point is on the edge of the DEM or not


def isEdgePoint(x, y, array):
    isWestSide = x > 0 and array[x-1][y] == noDataValue
    isEastSide = x < array.shape[0] - \
        1 and array[x+1][y] == noDataValue
    isNorthSide = y > 0 and array[x][y-1] == noDataValue
    isSouthSide = y < array.shape[1] - \
        1 and array[x][y+1] == noDataValue
    return (isWestSide or isEastSide or isNorthSide or isSouthSide)

# Adds points to the vertices and normals to signify the side of the mesh extrusion
def addSidePoints(x,  y, v, n, edge_height):
    for i in range(int(edge_height), int(bottomLevel), -1):
        v.append([x, y, i])
        n.append([1, 0, 0])
