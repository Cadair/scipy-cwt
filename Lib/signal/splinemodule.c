#include "Python.h"
#include "Numeric/arrayobject.h"
#include <math.h>


#define PYERR(message) do {PyErr_SetString(PyExc_ValueError, message); goto fail;} while(0)
#define DATA(arr) ((arr)->data)
#define DIMS(arr) ((arr)->dimensions)
#define STRIDES(arr) ((arr)->strides)
#define ELSIZE(arr) ((arr)->descr->elsize)
#define OBJECTTYPE(arr) ((arr)->descr->type_num)
#define BASEOBJ(arr) ((PyArrayObject *)((arr)->base))
#define RANK(arr) ((arr)->nd)
#define ISCONTIGUOUS(m) ((m)->flags & CONTIGUOUS)
#define MIN(a,b) (((a) > (b)) ? (b) : (a))
#define MAX(a,b) (((a) > (b)) ? (a) : (b))

static void
convert_strides(instrides, convstrides, size, N)
     int *instrides;
     int *convstrides;
     int size, N;
{
  int n, bitshift;

  bitshift = -1;

  while (size != 0) {
    size >>= 1;
    bitshift++;
  }
  for (n = 0; n < N; n++) {
    convstrides[n] = instrides[n] >> (int )bitshift;
  }
}


static char doc_cspline2d[] = "ck = cspline2d(input, lambda=0.0, precision=None)\n\n Return the third-order B-spline coefficients over a regularly spaced input \n grid for the two-dimensional input image.  The lambda argument allows smoothing.\n";
 
static PyObject *cspline2d(PyObject *dummy, PyObject *args)
{
  PyObject *image=NULL;
  PyArrayObject *a_image=NULL, *ck=NULL;
  double lambda = 0.0;
  double precision = -1.0;
  int thetype, M, N, retval;
  int outstrides[2], instrides[2];

  if (!PyArg_ParseTuple(args, "O|dd", &image, &lambda, &precision)) return NULL;

  thetype = PyArray_ObjectType(image, PyArray_FLOAT);
  thetype = MIN(thetype, PyArray_DOUBLE);
  a_image = (PyArrayObject *)PyArray_FromObject(image, thetype, 2, 2);
  if (a_image == NULL) goto fail;
 
  ck = (PyArrayObject *)PyArray_FromDims(2,DIMS(a_image),thetype);
  if (ck == NULL) goto fail;
  M = DIMS(a_image)[0];
  N = DIMS(a_image)[1];

  convert_strides(STRIDES(a_image), instrides, ELSIZE(a_image), 2);
  outstrides[0] = N;
  outstrides[1] = 1;

  if (thetype == PyArray_FLOAT) {
    if ((precision <= 0.0) || (precision > 1.0)) precision = 1e-3;
    retval = S_cubic_spline2D((float *)DATA(a_image), (float *)DATA(ck), M, N, lambda, instrides, outstrides, precision);
  }
  else if (thetype == PyArray_DOUBLE) {
    if ((precision <= 0.0) || (precision > 1.0)) precision = 1e-6;
    retval = D_cubic_spline2D((double *)DATA(a_image), (double *)DATA(ck), M, N, lambda, instrides, outstrides, precision);
  }

  if (retval == -3) PYERR("Precision too high.  Error did not converge.");
  if (retval < 0) PYERR("Problem occured inside routine");

  Py_DECREF(a_image);
  return PyArray_Return(ck);
 
 fail:
  Py_XDECREF(a_image);
  Py_XDECREF(ck);
  return NULL;

}

static char doc_qspline2d[] = "qk = qspline2d(input, lambda=0.0, precision=None)\n\n Return the second-order B-spline coefficients over a regularly spaced input \n grid for the two-dimensional input image.  The lambda argument allows smoothing.\n";
 
static PyObject *qspline2d(PyObject *dummy, PyObject *args)
{
  PyObject *image=NULL;
  PyArrayObject *a_image=NULL, *ck=NULL;
  double lambda = 0.0;
  double precision = -1.0;
  int thetype, M, N, retval;
  int outstrides[2], instrides[2];

  if (!PyArg_ParseTuple(args, "O|dd", &image, &lambda, &precision)) return NULL;

  if (lambda != 0.0) PYERR("Smoothing spline not yet implemented.");

  thetype = PyArray_ObjectType(image, PyArray_FLOAT);
  thetype = MIN(thetype, PyArray_DOUBLE);
  a_image = (PyArrayObject *)PyArray_FromObject(image, thetype, 2, 2);
  if (a_image == NULL) goto fail;
 
  ck = (PyArrayObject *)PyArray_FromDims(2,DIMS(a_image),thetype);
  if (ck == NULL) goto fail;
  M = DIMS(a_image)[0];
  N = DIMS(a_image)[1];

  convert_strides(STRIDES(a_image), instrides, ELSIZE(a_image), 2);
  outstrides[0] = N;
  outstrides[1] = 1;

  if (thetype == PyArray_FLOAT) {
    if ((precision <= 0.0) || (precision > 1.0)) precision = 1e-3;
    retval = S_quadratic_spline2D((float *)DATA(a_image), (float *)DATA(ck), M, N, lambda, instrides, outstrides, precision);
  }
  else if (thetype == PyArray_DOUBLE) {
    if ((precision <= 0.0) || (precision > 1.0)) precision = 1e-6;
    retval = D_quadratic_spline2D((double *)DATA(a_image), (double *)DATA(ck), M, N, lambda, instrides, outstrides, precision);
  }

  if (retval == -3) PYERR("Precision too high.  Error did not converge.");
  if (retval < 0) PYERR("Problem occured inside routine");

  Py_DECREF(a_image);
  return PyArray_Return(ck);
 
 fail:
  Py_XDECREF(a_image);
  Py_XDECREF(ck);
  return NULL;

}


static char doc_FIRsepsym2d[] = "out = sepsym2d(in, hrow, hcol)\n\n Convolve the rank-2 input array with the separable filter defined by the rank-1\n arrays hrow, and hcol. Boundary conditions are mirror symmetric.\n This function inverts the B-spline.";
 
static PyObject *FIRsepsym2d(PyObject *dummy, PyObject *args)
{
  PyObject *image=NULL, *hrow=NULL, *hcol=NULL;
  PyArrayObject *a_image=NULL, *a_hrow=NULL, *a_hcol=NULL, *out=NULL;
  int thetype, M, N, ret;
  int outstrides[2], instrides[2];

  if (!PyArg_ParseTuple(args, "OOO", &image, &hrow, &hcol)) return NULL;

  thetype = PyArray_ObjectType(image, PyArray_FLOAT);
  thetype = MIN(thetype, PyArray_CDOUBLE);
  a_image = (PyArrayObject *)PyArray_FromObject(image, thetype, 2, 2);
  a_hrow = (PyArrayObject *)PyArray_ContiguousFromObject(hrow, thetype, 1, 1);
  a_hcol = (PyArrayObject *)PyArray_ContiguousFromObject(hcol, thetype, 1, 1);
  
  if ((a_image == NULL) || (a_hrow == NULL) || (a_hcol==NULL)) goto fail;
  
  out = (PyArrayObject *)PyArray_FromDims(2,DIMS(a_image),thetype);
  if (out == NULL) goto fail;
  M = DIMS(a_image)[0];
  N = DIMS(a_image)[1];

  convert_strides(STRIDES(a_image), instrides, ELSIZE(a_image), 2);
  outstrides[0] = N;
  outstrides[1] = 1;

  switch (thetype) {
  case PyArray_FLOAT:
    ret = S_separable_2Dconvolve_mirror((float *)DATA(a_image), 
					(float *)DATA(out), M, N,
					(float *)DATA(a_hrow), 
					(float *)DATA(a_hcol),
					DIMS(a_hrow)[0], DIMS(a_hcol)[0], 
					instrides, outstrides);
    break;
  case PyArray_DOUBLE:
    ret = D_separable_2Dconvolve_mirror((double *)DATA(a_image), 
					(double *)DATA(out), M, N, 
					(double *)DATA(a_hrow), 
					(double *)DATA(a_hcol),
					DIMS(a_hrow)[0], DIMS(a_hcol)[0], 
					instrides, outstrides);
    break;
#ifdef __GNUC__
  case PyArray_CFLOAT:
    ret = C_separable_2Dconvolve_mirror((__complex__ float *)DATA(a_image), 
					(__complex__ float *)DATA(out), M, N, 
					(__complex__ float *)DATA(a_hrow), 
					(__complex__ float *)DATA(a_hcol),
					DIMS(a_hrow)[0], DIMS(a_hcol)[0], 
					instrides, outstrides);
    break;
  case PyArray_CDOUBLE:
    ret = Z_separable_2Dconvolve_mirror((__complex__ double *)DATA(a_image), 
					(__complex__ double *)DATA(out), M, N, 
					(__complex__ double *)DATA(a_hrow), 
					(__complex__ double *)DATA(a_hcol),
					DIMS(a_hrow)[0], DIMS(a_hcol)[0], 
					instrides, outstrides);
    break;
#endif
  default:
    PYERR("Incorrect type.");
  }
  
  if (ret < 0) PYERR("Problem occured inside routine.");

  Py_DECREF(a_image);
  Py_DECREF(a_hrow);
  Py_DECREF(a_hcol);
  return PyArray_Return(out);
 
 fail:
  Py_XDECREF(a_image);
  Py_XDECREF(a_hrow);
  Py_XDECREF(a_hcol);
  Py_XDECREF(out);
  return NULL;

}

static char doc_IIRsymorder1[] = "out = symiirorder1(in, c0, z1 [, precision])";
 
static PyObject *IIRsymorder1(PyObject *dummy, PyObject *args)
{
  PyObject *sig=NULL;
  PyArrayObject *a_sig=NULL, *out=NULL;
  Py_complex c0, z1;
  double precision = -1.0;
  int thetype, N, ret;
  int outstrides, instrides;

  if (!PyArg_ParseTuple(args, "ODD|d", &sig, &c0, &z1, &precision))
    return NULL;

  thetype = PyArray_ObjectType(sig, PyArray_FLOAT);
  thetype = MIN(thetype, PyArray_CDOUBLE);
  a_sig = (PyArrayObject *)PyArray_FromObject(sig, thetype, 1, 1);
  
  if ((a_sig == NULL)) goto fail;
  
  out = (PyArrayObject *)PyArray_FromDims(1,DIMS(a_sig),thetype);
  if (out == NULL) goto fail;
  N = DIMS(a_sig)[0];

  convert_strides(STRIDES(a_sig), &instrides, ELSIZE(a_sig), 1);
  outstrides = 1;

  switch (thetype) {
  case PyArray_FLOAT:
    {
      float rc0 = c0.real;
      float rz1 = z1.real;

      if ((precision <= 0.0) || (precision > 1.0)) precision = 1e-6;      
      ret = S_IIR_forback1 (rc0, rz1, (float *)DATA(a_sig), 
			    (float *)DATA(out), N,
			    instrides, outstrides, (float )precision);
    }
    break;
  case PyArray_DOUBLE:
    {
      double rc0 = c0.real;
      double rz1 = z1.real;

      if ((precision <= 0.0) || (precision > 1.0)) precision = 1e-11;
      ret = D_IIR_forback1 (rc0, rz1, (double *)DATA(a_sig), 
			    (double *)DATA(out), N,
			    instrides, outstrides, precision);
    }
    break;
#ifdef __GNUC__
  case PyArray_CFLOAT:
    {
      __complex__ float zc0 = c0.real + 1.0i*c0.imag;
      __complex__ float zz1 = z1.real + 1.0i*z1.imag;      
      if ((precision <= 0.0) || (precision > 1.0)) precision = 1e-6;
      ret = C_IIR_forback1 (zc0, zz1, (__complex__ float *)DATA(a_sig), 
			    (__complex__ float *)DATA(out), N,
			    instrides, outstrides, (float )precision);
    }
    break;
  case PyArray_CDOUBLE:
    {
      __complex__ double zc0 = c0.real + 1.0i*c0.imag;
      __complex__ double zz1 = z1.real + 1.0i*z1.imag;      
      if ((precision <= 0.0) || (precision > 1.0)) precision = 1e-11;
      ret = Z_IIR_forback1 (zc0, zz1, (__complex__ double *)DATA(a_sig), 
			    (__complex__ double *)DATA(out), N,
			    instrides, outstrides, precision);
    }
    break;
#endif
  default:
    PYERR("Incorrect type.");
  }
  
  if (ret < 0) PYERR("Problem occured inside routine.");

  Py_DECREF(a_sig);
  return PyArray_Return(out);
 
 fail:
  Py_XDECREF(a_sig);
  Py_XDECREF(out);
  return NULL;

}


static char doc_IIRsymorder2[] = "out = symiirorder2(in, r, omega [, precision])";
 
static PyObject *IIRsymorder2(PyObject *dummy, PyObject *args)
{
  PyObject *sig=NULL;
  PyArrayObject *a_sig=NULL, *out=NULL;
  double r, omega;
  double precision = -1.0;
  int thetype, N, ret;
  int outstrides, instrides;

  if (!PyArg_ParseTuple(args, "Odd|d", &sig, &r, &omega, &precision))
    return NULL;

  thetype = PyArray_ObjectType(sig, PyArray_FLOAT);
  thetype = MIN(thetype, PyArray_DOUBLE);
  a_sig = (PyArrayObject *)PyArray_FromObject(sig, thetype, 1, 1);
  
  if ((a_sig == NULL)) goto fail;
  
  out = (PyArrayObject *)PyArray_FromDims(1,DIMS(a_sig),thetype);
  if (out == NULL) goto fail;
  N = DIMS(a_sig)[0];

  convert_strides(STRIDES(a_sig), &instrides, ELSIZE(a_sig), 1);
  outstrides = 1;

  switch (thetype) {
  case PyArray_FLOAT:
    if ((precision <= 0.0) || (precision > 1.0)) precision = 1e-6;      
    ret = S_IIR_forback2 (r, omega, (float *)DATA(a_sig), 
			  (float *)DATA(out), N,
			  instrides, outstrides, precision);
    break;
  case PyArray_DOUBLE:
    if ((precision <= 0.0) || (precision > 1.0)) precision = 1e-11;
    ret = D_IIR_forback2 (r, omega, (double *)DATA(a_sig), 
			  (double *)DATA(out), N,
			  instrides, outstrides, precision);
    break;
  default:
    PYERR("Incorrect type.");
  }
  
  if (ret < 0) PYERR("Problem occured inside routine.");

  Py_DECREF(a_sig);
  return PyArray_Return(out);
 
 fail:
  Py_XDECREF(a_sig);
  Py_XDECREF(out);
  return NULL;

}


static struct PyMethodDef toolbox_module_methods[] = {
        {"cspline2d", cspline2d, METH_VARARGS, doc_cspline2d},
        {"qspline2d", qspline2d, METH_VARARGS, doc_qspline2d},
        {"sepfir2d", FIRsepsym2d, METH_VARARGS, doc_FIRsepsym2d},
	{"symiirorder1", IIRsymorder1, METH_VARARGS, doc_IIRsymorder1},
	{"symiirorder2", IIRsymorder2, METH_VARARGS, doc_IIRsymorder2}, 
	{NULL,		NULL, 0}		/* sentinel */
};

/* Initialization function for the module (*must* be called initXXXXX) */

DL_EXPORT(void) initspline() {
	PyObject *m, *d, *s;
	
	/* Create the module and add the functions */
	m = Py_InitModule("spline", toolbox_module_methods);

	/* Import the C API function pointers for the Array Object*/
	import_array();

	/* Add some symbolic constants to the module */
	d = PyModule_GetDict(m);

	s = PyString_FromString("0.2");
	PyDict_SetItemString(d, "__version__", s);
	Py_DECREF(s);

	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module array");
}















