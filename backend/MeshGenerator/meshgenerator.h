#ifndef MESHGENERATOR_H
#define MESHGENERATOR_H

#include "MeshGenerator_global.h"
#include <fstream>

struct Parameters;

extern "C" MESHGENERATOR_EXPORT void generateSTL(float* v, int width, int height,
                                                 float noDataValue, float lineWidth, float bottomLevel, const char* filename);

void writeFace(float vertices[3][3], Parameters& p, FILE* fp);
void addSideFace(float x1, float x2, float y1, float y2, Parameters& p, FILE* fp);
bool isEdgePoint(int x, int y, Parameters p);
float getArrayValue(int xIndex, int yIndex, Parameters p);

#endif // MESHGENERATOR_H
