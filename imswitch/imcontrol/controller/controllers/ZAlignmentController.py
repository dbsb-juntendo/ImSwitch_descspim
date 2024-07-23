from ..basecontrollers import ImConWidgetController
import time

class ZAlignmentController(ImConWidgetController):
    """ Linked to ZAlignmentWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # connect the buttons
        self._widget.sigSavePosOneClicked.connect(self.save_pos1)
        self._widget.sigSavePosTwoClicked.connect(self.save_pos2)
        self._widget.sigZstepSetClicked.connect(self.setZstep)
        self._widget.sigCalculateClicked.connect(self.calculate)
        self._widget.sigMovePosOneClicked.connect(self.moveToPos1)
        self._widget.sigMovePosTwoClicked.connect(self.moveToPos2)
        self._widget.sigUpdateStagesClicked.connect(self.updateStages)

    # Functions
    def _getStages(self):
        stages = [(pName, pManager) for pName, pManager in self._master.positionersManager if pManager.forPositioning]
        if len(stages) != 2:
            self._logger.error('Need two positioners for ZAlignmentWidget.')
            return
        else:
            camera_stage = None
            sample_stage = None
            for stage in stages:
                if stage[0].lower().startswith('camera'):
                    camera_stage = stage
                else:
                    sample_stage = stage
            return sample_stage, camera_stage

    def getPos(self):
        """ Get the current position of the camera and sample stage. """
        # get positioner names
        camera_stage, sample_stage = self._getStages()
        camera_pos = self._master.positionersManager[camera_stage[0]].getPosition(camera_stage[1].axes[0])
        sample_pos = self._master.positionersManager[sample_stage[0]].getPosition(sample_stage[1].axes[0])
        return camera_pos, sample_pos
    
    def save_pos1(self):
        sam_pos, cam_pos = self.getPos()
        self._widget.update_pos1(sam_pos, cam_pos)
        #setSharedAttribute etc, needed?

    def save_pos2(self):
        sam_pos, cam_pos = self.getPos()
        self._widget.update_pos2(sam_pos, cam_pos)
        #setSharedAttribute etc, needed?
    
    def setZstep(self):
        return self._widget.getZstep()
        #setSharedAttribute etc, needed?
    
    def calculate(self):
        posConvFac = [(pName, pManager) for pName, pManager in self._master.positionersManager if pManager.forPositioning][0][1]._posConvFac
        posConvFac = (1 / posConvFac) * 1000           # to µm/du
        req_zstep = self._widget.getZstep()            # in µm
        req_zstep_du = req_zstep * posConvFac * 1000   # in du
        
        pos1s, pos1c, pos2s, pos2c  = [float(i.split()[1]) for i in self._widget.getPositions()]
        factor = abs(pos1s - pos2s) / abs(pos1c - pos2c)
        du_camera = [i for i in range(1, 40)]                          # device units camera
        dist_camera = [i*posConvFac for i in du_camera]               # distance camera in µm
        dist_sample = [i*factor for i in dist_camera]                   # distance sample in µm
        du_sample = [i/posConvFac for i in dist_sample]                 # device units sample
        result = [(i, du) for i, du in enumerate(du_sample) if abs(round(du) - du) <= 0.1]
        closest_du = min(result, key=lambda x: abs(x[1] - req_zstep_du))
        sample_zstep = closest_du[1] * posConvFac
        camera_zstep = dist_camera[closest_du[0]]
        self._widget.updateResults(factor, sample_zstep, camera_zstep)
        
    def moveToPos1(self):
        pos1_s, pos1_c = self._widget.getPositions()[0:2]
        self.moveSampleCamera(pos1_c, pos1_s)

    def moveToPos2(self):
        pos2_s, pos2_c = self._widget.getPositions()[2:4]
        self.moveSampleCamera(pos2_c, pos2_s)

    def moveSampleCamera(self, pos_c, pos_s):
        sample_stage, camera_stage = self._getStages()
        self._master.positionersManager[sample_stage[0]].moveAbsolute(float(pos_s.split()[1]), sample_stage[1].axes[0])       # move to pos1 sample
        self._commChannel.sigUpdateStagePosition.emit(sample_stage[0], sample_stage[1].axes[0])    #, new_pos)   # new  
        self._master.positionersManager[camera_stage[0]].moveAbsolute(float(pos_c.split()[1]), camera_stage[1].axes[0])       # move to pos1 camera                                 
        self._commChannel.sigUpdateStagePosition.emit(camera_stage[0], camera_stage[1].axes[0])    #, new_pos)   # new

    def updateStages(self):
        #TODO
        sample_stage, camera_stage = self._getStages()
        io_move_sample, io_move_camera = self._widget.getResultZstep()
        self._commChannel.sigUpdateRelDistance.emit(sample_stage[0], sample_stage[1].axes[0], io_move_sample)   # stage name, axis, rel_distance in um
        self._commChannel.sigUpdateRelDistance.emit(camera_stage[0], camera_stage[1].axes[0], io_move_camera)
        self._master.positionersManager[sample_stage[0]].set_rel_move_params(io_move_sample)
        self._master.positionersManager[camera_stage[0]].set_rel_move_params(io_move_camera)
        
