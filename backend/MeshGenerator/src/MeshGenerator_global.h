#ifndef MESHGENERATOR_GLOBAL_H
#define MESHGENERATOR_GLOBAL_H

#if defined(MESHGENERATOR_LIBRARY)
#ifdef _WIN32
#define MESHGENERATOR_EXPORT __declspec(dllexport)
#elif __GNUC__ >= 4
#define MESHGENERATOR_EXPORT __attribute__((visibility("default")))
#else
#define MESHGENERATOR_EXPORT
#endif
#else
#ifdef _WIN32
#define MESHGENERATOR_EXPORT __declspec(dllimport)
#else
#define MESHGENERATOR_EXPORT
#endif
#endif

#endif // MESHGENERATOR_GLOBAL_H
