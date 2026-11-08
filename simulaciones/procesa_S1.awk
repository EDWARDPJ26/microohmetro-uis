# Extrae niveles L (t=11.75 ms) y H (t=23.75 ms) por paso de RDUT y calcula R ratiometrica
/CURRENT STEP +PARAM/ { r=$NF; if (r!=last){ step++; rd[step]=r; last=r }  }
/^  TIME/ { if (index($0,"V(VSET)")) tab=1; else if (index($0,"V(AIN1)")) tab=2; else tab=3 }
/^ +[0-9]\.[0-9]+E[-+][0-9]+ / {
  t=$1+0
  if (tab==1) { if (t>0.01174 && t<0.01176){ vdL[step]=$3; vrL[step]=$4; vsL[step]=$2 } if (t>0.02374 && t<0.02376){ vdH[step]=$3; vrH[step]=$4; vsH[step]=$2 } }
  if (tab==2) { if (t>0.02374 && t<0.02376){ smin[step]=$2; splus[step]=$3; gate[step]=$4 } if (t>0.01174 && t<0.01176){ sminL[step]=$2 } }
  if (tab==3) { if (t>0.02374 && t<0.02376){ vpm[step]=$2 } }
}
END {
  printf "RDUT_ohm,IL_A,IH_A,VdutL_V,VdutH_V,VrsL_V,VrsH_V,Rmed_ohm,Error_pct,Smin_L_V,Smin_H_V,Splus_H_V,Vgate_H_V,Vds_pmos_H_V\n"
  for (i=1;i<=step;i++){ R=0.12*(vdH[i]-vdL[i])/(vrH[i]-vrL[i]); e=(rd[i]+0!=0)?(R-rd[i])/rd[i]*100:0
    printf "%s,%.5f,%.5f,%.6e,%.6e,%.6e,%.6e,%.6e,%.4f,%.4f,%.4f,%.4f,%.4f,%s\n", rd[i], vrL[i]/0.12, vrH[i]/0.12, vdL[i], vdH[i], vrL[i], vrH[i], R, e, sminL[i], smin[i], splus[i], gate[i], "-" }
}
