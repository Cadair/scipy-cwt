#include <stdio.h>
#include <math.h>
#include <stdlib.h>

/* Generally useful structures for passing data into and out of
   subroutines.  Used in the generic routines instead of the
   Python Specific structures so that the routines can be easily
   grabbed and used in another scripting language */

typedef struct {
  char *data;
  int elsize;
} Generic_ptr;

typedef struct {
  char *data;
  int numels;
  int elsize;
  char *zero;        /* Pointer to Representation of zero */
} Generic_Vector;

typedef struct {
  char *data;
  int  nd;
  int  *dimensions;
  int  elsize;
  int  *strides;
  char *zero;         /* Pointer to Representation of zero */
} Generic_Array;

typedef void (MultAddFunction) (char *, int, char *, int, char *, int *, int *, int, int, int, int *, int *, unsigned long *);

typedef void (BasicFilterFunction) (char *, char *,  char *, char *, char *, int, unsigned int, int, int);

static int index_out_of_bounds(int *, int *, int );
static long compute_offsets (unsigned long *, long *, int *, int *, int *, int *, int);
static int increment(int *, int, int *);

static void convolveND(Generic_Array *, Generic_Array *, Generic_Array *, MultAddFunction *, int);
static void RawFilter(Generic_Vector, Generic_Vector, Generic_Array, Generic_Array, Generic_Array *, Generic_Array *, BasicFilterFunction *, int);
