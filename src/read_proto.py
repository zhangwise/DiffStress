## methods related with proto files
import numpy as np
from glob import glob
from MP import ssort
ind_swap = ssort.ind_swap
from os import sep
from MP.mat import mech

def read(fn='../dat/23JUL12/23JUL12_0021Data4Phi135.txt'):
    dlines = open(fn,'r').readlines()

    # information based on the filename
    fn = fn.split(sep)[-1]
    date = fn.split('_')[0]
    fn = fn.split('_')[1]
    nth = int(fn.split('Data')[0])
    nscan = int(fn.split('Data')[1][0])
    phi = float(fn.split('Phi')[1].split('.txt')[0])

    # format
    ihead = [2,10]
    d_block = dlines[11:]

    kount = 0
    n = 0
    ibreak=False
    detectors = []
    while not(ibreak):
        nl = 12
        i0 = 0 + n*nl
        i1 = i0 + nl

        try:
            if d_block[i0].split()[0]!='Detector':
                ibreak=True
        except:
            ibreak=True

        if not(ibreak):
            n= n + 1
            b = d_block[i0:i1]
            newdet = Det(b,phi)
            detectors.append(newdet)

        kount = kount + 1
        if (kount>5): raise IOError, 'Nasty format match'
    return detectors

class ProtoExp:
    """
    a Proto Exp contains a number of psi scans for various phis
    for a various deformation steps
    """
    def __init__(self,path='../dat/23JUL12',fref=None):

        if fref==None:
            raise IOError, 'Not further developed yet.'
            # fns = glob('%s%s*.txt'%(path,sep))
            # scan_i = []
            # for i in range(len(fns)):
            #     try:
            #         j = int(fns[i].split(sep)[-1].\
            #                 split('_')[1].split('Data')[0])
            #         if j in scan_i:
            #             pass
            #         else: scan_i.append(j)
            #     except: pass

            # self.nscan = len(scan_i)

            # self.fns = fns
            # for i in range(self.nscan):
            #     fs = glob('%s%s*_%sData*.txt'%(
            #         path,sep,
            #         str(scan_i[i]).zfill(4)))

        if fref!=None:
            if path==None: path = '.'
            fref = '%s%s%s'%(path,sep,fref)

            #print fref

            flab, e1, e2 = np.loadtxt(
                fref,skiprows=2,dtype='str').T

            e1 = np.array(e1,dtype='float')
            e2 = np.array(e2,dtype='float')

            # assuming that it is a BB mode
            self.flow = mech.FlowCurve()
            self.flow.get_strain(e1,0,0)
            self.flow.get_strain(e2,1,1)
            e3 = - e1 - e2
            self.flow.get_strain(e3,2,2)
            self.flow.set_zero_shear_strain()
            self.flow.get_vm_strain()

            self.nscan = len(flab)
            self.P_scan = []

            nphis = []; npsis=[]

            self.phis = []
            self.psis = []

            for i in range(self.nscan):
                dum = '%s%s%sData*.txt'%(path,sep,flab[i])
                fs = glob(dum)
                nphi = len(fs)
                self.P_scan.append(ProtoScan())
                for iphi in range(nphi):
                    self.P_scan[i].add_phi(ProtoPhi(fn=fs[iphi]))
                self.P_scan[i].get_dspc_avg()
                self.P_scan[i].get_epshkl_davg()

                #for i in range(self.nscan):
                nphis.append(self.P_scan[i].nphi)
                for j in range(len(self.P_scan[i].protophi)):
                    npsis.append(self.P_scan[i].protophi[j].npsi)
                    self.phis.append(self.P_scan[i].protophi[j].phi)
                    self.psis.append(self.P_scan[i].protophi[j].psis)

            nphis=np.unique(nphis)
            npsis=np.unique(npsis)
            self.phis=np.unique(self.phis)
            self.psis=np.unique(np.array(self.psis))

            if (len(nphis)!=1):
                raise IOError, 'phi setting is not uniform'
            if (len(npsis)!=1):
                raise IOError, 'phi setting is not uniform'

            self.nphis=nphis[0]
            self.npsis=npsis[0]

        self.phi= self.phis
        self.psi= self.psis

        self.nphi = len(self.phis)
        self.nphis = self.nphi
        self.npsi = len(self.psis)
        self.npsis = self.npsi


    def list(self):
        print '#--------------------------------------------#'
        print '%8s %4i'%('nphis:', self.nphis),
        for i in range(len(self.phis)):
            print '%+4i'%self.phis[i],
        print ''
        print '%8s %4i'%('npsis:', self.npsis),
        for i in range(3):
            print '%+4.1f'%self.psis[i],
        print ' ... ',
        for i in range(1):
            print '%+4.1f'%self.psis[-i-1],
        print ''
        print '%8s %3i'%('nsteps:', len(self.P_scan))
        print '%8s'%'E_{VM}:',
        for i in range(3):
            print '%4.2f'%(self.flow.epsilon_vm[i]),
        print ' ...' ,
        for i in range(1):
            print '%4.2f'%(self.flow.epsilon_vm[-i-1]),
        print
        print '#--------------------------------------------#'

    def get_ehkl(self):
        nstp = self.flow.nstp
        nphi = self.nphi
        npsi = self.npsi
        ehkl = np.zeros((nstp,nphi,npsi))
        for istp in range(nstp):
            P = self.P_scan[istp]
            d_avg = P.d_avg
            for iphi in range(nphi):
                p_phi = P.protophi[iphi]
                for ipsi in range(npsi):
                    p_psi = p_phi.ppscans[ipsi]
                    ehkl[istp,iphi,ipsi]\
                        = (p_psi.dspc-d_avg)/d_avg
        self.ehkl = ehkl

    def assign_d0(self,d0=None):
        """
        Assign d0 and calculate eps_{hkl}
        """
        nstp = self.flow.nstp
        nphi = self.nphi
        npsi = self.npsi
        ehkl = np.zeros((nstp,nphi,npsi))
        for istp in range(nstp):
            P = self.P_scan[istp]
            for iphi in range(nphi):
                p_phi = P.protophi[iphi]
                for ipsi in range(npsi):
                    p_psi = p_phi.ppscans[ipsi]
                    ehkl[istp,iphi,ipsi]\
                        = (p_psi.dspc-d0)/d0
        self.ehkl=ehkl

    def plot_all(self):
        from MP.lib import mpl_lib
        wide_fig = mpl_lib.wide_fig
        tune_xy_lim = mpl_lib.tune_xy_lim
        from MP.lib import axes_label
        from MP.lib import mpl_lib
        import matplotlib as mpl
        deco = axes_label.__deco__
        rm_inner =mpl_lib.rm_inner
        ticks_bin_u = mpl_lib.ticks_bins_ax_u

        figs = wide_fig(nw=self.nphi,w0=0,w1=0,
                        left=0.2,right=0.15,
                        useOffset=False)

        mx = max(self.flow.epsilon_vm)
        mn = min(self.flow.epsilon_vm)
        cmap, c = mpl_lib.norm_cmap(
            mx = mx, mn=mn)

        for i in range(self.flow.nstp):
            eps = self.flow.epsilon_vm[i]
            cl = c.to_rgba(eps)
            for j in range(self.nphi):
                #X = np.sin(self.psi*np.pi/180.)**2
                X = self.psi
                Y = []
                for ipsi in range(self.npsi):
                    y = self.P_scan[i].protophi[j].\
                        ppscans[ipsi].dspc
                    Y.append(y)
                figs.axes[j].plot(X,Y,'-x',color=cl)
                if i==0:
                    figs.axes[j].set_title(
                        r'$\phi: %3.1f^\circ{}$'%self.phi[j])



        ticks_bin_u(figs.axes,n=4)
        deco(figs.axes[0],iopt=4)
        tune_xy_lim(figs.axes)
        rm_inner(figs.axes)

        b = figs.axes[-1].get_position()
        axcb = figs.add_axes([0.88,b.y0,0.03,b.y1-b.y0])
        mpl_lib.add_cb(axcb,cmap=cmap,filled=True,
                       ylab='Equivalent Strain')

    def plot(self,istps=[-1]):
        ps = []
        nstps = len(istps)
        for istp in range(len(istps)):
            ps.append(self.P_scan[istp])


        import matplotlib.pyplot as plt
        import MP
        from MP.lib import mpl_lib
        wide_fig = mpl_lib.wide_fig
        rm_lab   = mpl_lib.rm_lab
        rm_inner = mpl_lib.rm_inner
        ticks_bins_ax_u = mpl_lib.ticks_bins_ax_u
        ticks_bins_ax_u = mpl_lib.ticks_bins_ax_u
        tune_xy_lim  = mpl_lib.tune_xy_lim

        figs = wide_fig(nw=self.nphis,
                        nh=len(istps),
                        w0=0,w1=0,left=0.15,h0=0,h1=0,
                        up=0.1,down=0.1)
        # axest = []
        # for i in range(len(figs.axes)):
        #     tax = figs.axes[i].twinx()
        #     axest.append(tax)

        for istp in range(nstps):
            for iphi in range(self.nphis):
                iax = self.nphis * istp + iphi
                X = []
                Y = []; Y0 = []
                for ipsi in range(ps[istp].protophi[iphi].npsi):
                    x = np.sin(
                        ps[istp].protophi[iphi].\
                        ppscans[ipsi].psi*np.pi/180.)**2
                    y = ps[istp].protophi[iphi].\
                        ppscans[ipsi].dspc
                    y0 = ps[istp].protophi[iphi].\
                         ppscans[ipsi].ints
                    X.append(x); Y.append(y)
                    Y0.append(y0)


                figs.axes[iax].plot(X,Y,'-x')
                #axest[iax].plot(X,Y0,'-gx',alpha=0.5)

                if istp==nstps-1: figs.axes[iax].set_title(
                        r'$\phi=%3.1f^\circ{}$'%(ps[istp].\
                                         protophi[iphi].phi))

        ticks_bins_ax_u(figs.axes,n=5)
        tune_xy_lim = mpl_lib.tune_xy_lim(figs.axes)
        #tune_xy_lim = mpl_lib.tune_xy_lim(axest)
        rm_inner(figs.axes)

    def put_psi_offset(self,offset=0.0):
        """
        Adjust psi values by putting an offset
        """
        for i in range(self.flow.nstp):
            self.P_scan[i].put_psi_offset(offset)

        self.psi = self.psi + offset
        self.psis = self.psis + offset


class ProtoScan:
    """
    a set of protophi taken at a 'mechanical' state of interest
    """
    def __init__(self):
        self.protophi=[]
        self.nphi = 0
    def add_phi(self,protophi):
        self.protophi.append(protophi)
        self.nphi = len(self.protophi)
    def get_dspc_avg(self):
        dspc = []
        for i in range(len(self.protophi)):
            ps = self.protophi[i].ppscans
            for j in range(len(ps)):
                dspc.append(ps[j].dspc)
        dspc = np.array(dspc)
        self.dspc_avg = np.average(dspc)
        self.d_avg = np.average(dspc)
    def get_epshkl_davg(self):
        self.get_dspc_avg()
        for i in range(len(self.protophi)):
            ps = self.protophi[i].ppscans
            for j in range(len(ps)):
                ps[j].epshkl = (ps[j].dspc - self.d_avg)/self.d_avg
    def put_psi_offset(self,offset=0.0):
        for i in range(len(self.protophi)):
            self.protophi[i].put_psi_offset(offset)




class ProtoPhi:
    """
    A ProtoPhi contains a number of psi scans for a fixed phi
    """
    def __init__(self,fn='../dat/23JUL12/23JUL12_0021'\
                 'Data4Phi135.txt'):
        self.detectors = read(fn)
        self.phi = self.detectors[0].phi
        self.ndetectors = len(self.detectors)
        self.ndet = self.ndetectors

        # combine detectors for a single phi
        self.ppscans = []
        self.psis = []
        for i in range(self.ndet):
            det = self.detectors[i]
            for j in range(len(det.ppscans)):
                p = det.ppscans[j]
                self.psis.append(p.psi)
                self.ppscans.append(p)

        # sort self.ppscans based on self.psis
        self.psis, idx = ssort.shellSort(self.psis)
        self.ppscans = ind_swap(self.ppscans,idx)
        self.npsi = len(self.psis)
        ## sorts the PhiPsi scans in detectors based on phi-psi
    def plot(self):
        import matplotlib.pyplot as plt
        X=[]; Y=[]
        for i in range(self.npsi):
            x = self.ppscans[i].psi
            y = self.ppscans[i].dspc
            X.append(x)
            Y.append(y)
        plt.plot(X,Y,'-x')

    def put_psi_offset(self,offset=0.0):
        for idet in range(self.ndet):
            det = self.detectors[idet]
            for j in range(len(det.ppscans)):
                det.ppscans[j].put_psi_offset(offset)

        self.psis = self.psis + offset
        self.psis, idx = ssort.shellSort(self.psis)
        self.ppscans = ind_swap(self.ppscans,idx)
        self.npsi = len(self.psis)
            
class Det:
    """
    read a block of data lines belonging to a detector
    in proto file

    use only the self.ppscans

    """
    def __init__(self,bl,phi):
        self.phi=phi
        self.read_block(bl)
        self.sort_psi()
        # self.sort_sin2psi()
        self.add_ppscans()

    def read_block(self,b):
        self.idet = b[0].split()[-1]
        self.psis = np.array(map(float,b[2].split(':')[1].split()))
        self.sin2psi = np.sin(self.psis*np.pi/180.)**2
        self.dspc = np.array(map(float,b[4].split(':')[1].split()))
        self.th2  = np.array(map(float,b[5].split(':')[1].split()))
        self.fwhm  = np.array(map(float,b[7].split(':')[1].split()))
        self.ints  = np.array(map(float,b[10].split(':')[1].split()))
        self.npsis = len(self.psis)

    def sort_psi(self):
        self.psis, idx = ssort.shellSort(self.psis)
        self.sin2psi=ind_swap(self.sin2psi,idx)
        self.dspc=ind_swap(self.dspc,idx)
        self.th2=ind_swap(self.th2,idx)
        self.fwhm=ind_swap(self.fwhm,idx)
        self.ints=ind_swap(self.ints,idx)
        self.add_ppscans()

    def sort_sin2psi(self):
        self.sin2psi, idx = ssort.shellSort(self.sin2psi)
        self.psis=ind_swap(self.psis,idx)
        self.dspc=ind_swap(self.dspc,idx)
        self.th2=ind_swap(self.th2,idx)
        self.fwhm=ind_swap(self.fwhm,idx)
        self.ints=ind_swap(self.ints,idx)
        self.add_ppscans()

    def add_ppscans(self):
        self.ppscans=[]
        for i in range(self.npsis):
            self.ppscans.append(
                PhiPsiScan(psi=self.psis[i],
                           phi=self.phi,
                           dspc=self.dspc[i],
                           th2=self.th2[i],
                           fwhm=self.fwhm[i],
                           ints=self.ints[i]))

    def put_psi_offset(self,offset=0.0):
        """
        Put offset of psi...
        """
        for i in range(len(self.ppscans)):
            self.ppscans[i].put_psi_offset(offset=offset)

        # any systematic offset doesn't change the order of psi
        # however, it may change the order of sin2psi....
        self.psis = self.psis + offset
        self.sin2psi = np.sin(self.psis*np.pi/180.)**2

        print 'An offset value for psi was introduced.'
        print 'Consider redoing sort_sin2psi if necessary'

class PhiPsiScan:
    def __init__(self,psi,phi,dspc,th2,fwhm,ints):
        self.psi=psi
        self.phi=phi
        self.dspc=dspc
        self.th2=th2
        self.fwhm=fwhm
        self.ints=ints
        self.xy_coord()
    def xy_coord(self):
        from phikhi import psikhi2cart
        conv = psikhi2cart.conv
        self.x, self.y = conv(p=self.phi,k=self.psi)
    def put_psi_offset(self,offset=0.0):
        """
        In experiments, sometimes the beta zero position
        requires a fix aftermath, if the symmetry was not
        properly set at the beginning.
        """
        self.psi=self.psi + offset
