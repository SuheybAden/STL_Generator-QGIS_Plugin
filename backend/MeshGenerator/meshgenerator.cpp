#include "meshgenerator.h"

#include <errno.h>
#include <stdio.h>
#include <string.h>

struct Parameters
{
    int width;
    int height;
    float noDataValue;
    float lineWidth;
    float bottomLevel;
    unsigned int numTriangles;
    float* v;
    const char* filename;
};

MESHGENERATOR_EXPORT void generateSTL(float* v, int width, int height, float noDataValue,
                                   float lineWidth, float bottomLevel, const char* filename)
{
//    Logger("Started generateSTL function");
    struct Parameters p = { width, height, noDataValue, lineWidth, bottomLevel, 0, v, filename};

    unsigned char header[80] = { 0 };

    //Logger(filename);
    // Open STL file that will be written to
    FILE* fp;
    errno_t err = fopen_s(&fp, p.filename, "wb+");
    if (err) {
        //Logger("Error opening up the file");
        fprintf(stderr, "cannot open file '%s': %s\n",
                p.filename, strerror(errno));
        return;
    }


    // Write the placeholder values for the header and number of triangles
    fwrite(&header, sizeof(header), 1, fp);
    fwrite(&p.numTriangles, sizeof(p.numTriangles), 1, fp);
    //Logger("Wrote header to file");
    //Logger("No data value is " + std::to_string(noDataValue));

    // Iterate through each point in the array and determine what triangles need to be written
    for (float x = 0; x < width - 1; x++) {
        for (float y = 0; y < height - 1; y++) {
            //printf("Trying to get the array value at (%d, %d): %f\n", x, y, getArrayValue(x, y, p));
            // Write top left triangle if it exists
            if (getArrayValue(x, y, p) != noDataValue &&
                getArrayValue(x + 1, y, p) != noDataValue &&
                getArrayValue(x, y + 1, p) != noDataValue) {
                //printf("Top left triangle exists\n");
                // Write top and bottom faces
                float topLeftFace[3][3] = { {x, y, getArrayValue(x, y, p)},
                                           {x + 1, y, getArrayValue(x + 1, y, p)},
                                           {x, y + 1, getArrayValue(x, y + 1, p)} };
                float topLeftFace_bottom[3][3] = { {x, y, bottomLevel},
                                                  {x + 1, y, bottomLevel},
                                                  {x, y + 1, bottomLevel} };
                writeFace(topLeftFace, p, fp);
                writeFace(topLeftFace_bottom, p, fp);

                // Write side faces
                addSideFace(x, y, x + 1, y, p, fp);
                addSideFace(x, y, x, y + 1, p, fp);
                addSideFace(x + 1, y, x, y + 1, p, fp);
            }
            // Write bottom right triangle if it exists
            if (getArrayValue(x + 1, y + 1, p) != noDataValue &&
                getArrayValue(x + 1, y, p) != noDataValue &&
                getArrayValue(x, y + 1, p) != noDataValue) {
                //printf("Top right triangle exists\n");

                // Write top and bottom faces
                float bottomRightFace[3][3] = { {x + 1, y + 1, getArrayValue(x + 1, y + 1, p)},
                                               {x, y + 1, getArrayValue(x, y + 1, p)},
                                               {x + 1, y, getArrayValue(x + 1, y, p)} };
                float bottomRightFace_bottom[3][3] = { {x + 1, y + 1, bottomLevel},
                                                      {x, y + 1, bottomLevel},
                                                      {x + 1, y, bottomLevel} };
                writeFace(bottomRightFace, p, fp);
                writeFace(bottomRightFace_bottom, p, fp);

                // Write side faces
                addSideFace(x + 1, y + 1, x + 1, y, p, fp);
                addSideFace(x + 1, y + 1, x, y + 1, p, fp);
                addSideFace(x + 1, y, x, y + 1, p, fp);
            }
        }
    }
    //Logger("Finished looping through array");

    // Update header and number of triangles
    fseek(fp, 0, SEEK_SET);
    fwrite(&header, sizeof(header), 1, fp);
    fwrite(&p.numTriangles, sizeof(p.numTriangles), 1, fp);
    fclose(fp);
    //Logger("Updated header and closed file");
}

float getArrayValue(int xIndex, int yIndex, Parameters p) {
    int index = xIndex * (p.height) + yIndex;
    //printf("The index is: %d\n", index);
    return p.v[index];
}

void writeFace(float vertices[3][3], Parameters& p, FILE* fp)
{
    //printf("Writing a face\n");
    // Increment count of triangles
    p.numTriangles++;

    // Write normal to STL file
    float normal[] = { 0.0, 0.0, 0.0 };
    fwrite(&normal, sizeof(normal), 1, fp);

    // Write vertices to STL file
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            if (j != 2) {
                vertices[i][j] *= p.lineWidth;
            }
            //printf("Writing vertex (%d, %d): %f\n", i, j, vertices[i][j]);
            fwrite(&vertices[i][j], sizeof(vertices[i][j]), 1, fp);
        }
    }

    // Write attribute byte count
    unsigned short count = 0;
    fwrite(&count, sizeof(count), 1, fp);
}

void addSideFace(float x1, float y1, float x2, float y2, Parameters& p, FILE* fp)
{

    if (isEdgePoint(x1, y1, p) && isEdgePoint(x2, y2, p)) {
        float sideFace1[3][3] = { {x1, y1, getArrayValue(x1, y1, p)},
                                 {x1, y1, p.bottomLevel},
                                 {x2, y2, getArrayValue(x2, y2, p)} };
        float sideFace2[3][3] = { {x1, y1, p.bottomLevel},
                                 {x2, y2, p.bottomLevel},
                                 {x2, y2, getArrayValue(x2, y2, p)} };
        writeFace(sideFace1, p, fp);
        writeFace(sideFace2, p, fp);
    }
}

bool isEdgePoint(int x, int y, Parameters p)
{
    // Checks if the point is on the boundary of the array
    if (x == 0 || x == p.width - 1 || y == 0 || y == p.height - 1) {
        //printf("Point (%i , %i) is an edge point: Along the border of the array\n", x, y);
        return true;
    }

    // Checks if the point is bordering a no data value
    for (int i = x - 1; i <= x + 1; i++) {
        for (int j = y - 1; j <= y + 1; j++) {
            float value = getArrayValue(i, j, p);
            if (value == p.noDataValue) {
                //printf("Point (%i , %i) is bordering a no data value. It's value is %f\n", x, y, getArrayValue(x, y, p));
                return true;
            }
        }
    }

    //printf("Point (%i , %i) is not an edge point: \n", x, y);
    return false;
}
