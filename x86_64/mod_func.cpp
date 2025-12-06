#include <stdio.h>
#include "hocdec.h"
extern int nrnmpi_myid;
extern int nrn_nobanner_;

extern "C" void _ca_hva_reg(void);
extern "C" void _cad_reg(void);

extern "C" void modl_reg() {
  if (!nrn_nobanner_) if (nrnmpi_myid < 1) {
    fprintf(stderr, "Additional mechanisms from files\n");
    fprintf(stderr, " \"ca_hva.mod\"");
    fprintf(stderr, " \"cad.mod\"");
    fprintf(stderr, "\n");
  }
  _ca_hva_reg();
  _cad_reg();
}
