#include "meshgenerator.h"

#include <stdio.h>
#include <string.h>
#include <fstream>

struct Parameters
{
    int width;
    int height;
    float noDataValue;
    float lineWidth;
    float bottomLevel;
    unsigned int numTriangles;
    float* v;
    const char *filename;
};

MESHGENERATOR_EXPORT void generateSTL(float* v, int width, int height, float noDataValue,
                                   float lineWidth, float bottomLevel, const char* filename)
{
    struct Parameters p = {width, height, noDataValue, lineWidth, bottomLevel, 0, v, filename};

    // Open STL file that will be written to
    std::ofstream file (p.filename, std::ios::out | std::ios::binary | std::ios::trunc);
    if (!file.is_open()) {
        return;
    }

    // Write the placeholder values for the header and number of triangles
    unsigned char header[80] = {0};
    file.write((char*)header, sizeof(header));
    file.write((char *)&p.numTriangles, sizeof(p.numTriangles));

    // Iterate through each point in the array and determine what triangles need to be written
    for (int x = 0; x < width - 1; x++)
    {
        for (int y = 0; y < height - 1; y++)
        {
            if (getArrayValue(x + 1, y, p) != noDataValue &&
                getArrayValue(x, y + 1, p) != noDataValue)
            {
                // Write top left triangle if it exists
                if (getArrayValue(x, y, p) != noDataValue)
                {
                    int section[3][2] = {
                        {x + 1, y},
                        {x, y + 1},
                        {x, y}};
                    writeSection(section, p, file);
                }
                // Write bottom right triangle if it exists
                if (getArrayValue(x + 1, y + 1, p) != noDataValue)
                {
                    int section[3][2] = {
                        {x + 1, y},
                        {x, y + 1},
                        {x + 1, y + 1}};
                    writeSection(section, p, file);
                }
            }

            else if (getArrayValue(x, y, p) != noDataValue &&
                     getArrayValue(x + 1, y + 1, p) != noDataValue)
            {
                // Write the top right triangle if it exists
                if (getArrayValue(x + 1, y, p) != noDataValue)
                {
                    int section[3][2] = {
                        {x + 1, y + 1},
                        {x, y},
                        {x + 1, y}};
                    writeSection(section, p, file);
                }

                // Write the bottom left triangle if it exists
                else if (getArrayValue(x, y + 1, p) != noDataValue)
                {
                    int section[3][2] = {
                        {x + 1, y + 1},
                        {x, y},
                        {x, y + 1}};
                    writeSection(section, p, file);
                }
            }
        }
    }

    // Update header and number of triangles
    file.seekp(0, std::ios::beg);
    file.write((char *)&header, sizeof(header));
    file.write((char *)&p.numTriangles, sizeof(p.numTriangles));
    file.close();
}

float getArrayValue(int xIndex, int yIndex, Parameters p) {
    int index = xIndex * (p.height) + yIndex;
    return p.v[index];
}

void writeSection(int vertices[3][2], Parameters &p, std::ofstream &file)
{
    // Write the top and bottom faces
    float topFace[3][3] = {{vertices[0][0], vertices[0][1], getArrayValue(vertices[0][0], vertices[0][1], p)},
                           {vertices[1][0], vertices[1][1], getArrayValue(vertices[1][0], vertices[1][1], p)},
                           {vertices[2][0], vertices[2][1], getArrayValue(vertices[2][0], vertices[2][1], p)}};
    float bottomFace[3][3] = {{vertices[0][0], vertices[0][1], p.bottomLevel},
                              {vertices[1][0], vertices[1][1], p.bottomLevel},
                              {vertices[2][0], vertices[2][1], p.bottomLevel}};
    writeFace(topFace, p, file);
    writeFace(bottomFace, p, file);

    // Write side faces
    addSideFace(vertices[0][0], vertices[0][1], vertices[1][0], vertices[1][1], p, file);
    addSideFace(vertices[0][0], vertices[0][1], vertices[2][0], vertices[2][1], p, file);
    addSideFace(vertices[1][0], vertices[1][1], vertices[2][0], vertices[2][1], p, file);
}

void writeFace(float vertices[3][3], Parameters &p, std::ofstream &file)
{
    // Increment count of triangles
    p.numTriangles++;

    // Write normal to STL file
    float normal[] = { 0.0, 0.0, 0.0 };
    file.write((char *)&normal, sizeof(normal));

    // Write vertices to STL file
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            if (j != 2) {
                vertices[i][j] *= p.lineWidth;
            }
            file.write((char *)&vertices[i][j], sizeof(vertices[i][j]));
        }
    }

    // Write attribute byte count
    unsigned short count = 0;
    file.write((char *)&count, sizeof(count));
}

void addSideFace(float x1, float y1, float x2, float y2, Parameters& p, std::ofstream& file)
{

    if (isEdgePoint(x1, y1, p) && isEdgePoint(x2, y2, p)) {
        float sideFace1[3][3] = { {x1, y1, getArrayValue(x1, y1, p)},
                                 {x1, y1, p.bottomLevel},
                                 {x2, y2, getArrayValue(x2, y2, p)} };
        float sideFace2[3][3] = { {x1, y1, p.bottomLevel},
                                 {x2, y2, p.bottomLevel},
                                 {x2, y2, getArrayValue(x2, y2, p)} };
        writeFace(sideFace1, p, file);
        writeFace(sideFace2, p, file);
    }
}

bool isEdgePoint(int x, int y, Parameters p)
{
    // Checks if the point is on the boundary of the array
    if (x == 0 || x == p.width - 1 || y == 0 || y == p.height - 1) {
        return true;
    }

    // Checks if the point is bordering a no data value
    for (int i = x - 1; i <= x + 1; i++) {
        for (int j = y - 1; j <= y + 1; j++) {
            float value = getArrayValue(i, j, p);
            if (value == p.noDataValue) {
                return true;
            }
        }
    }
    return false;
}
