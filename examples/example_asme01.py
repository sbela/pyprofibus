#!/usr/bin/env python3
#
# Simple pyprofibus example
#
# The hardware configuration is as follows:
#
#   v----------v
#   | 4 DI     |
#   | DC24V    |
#   |          |
#   |          |
#   | AS ME 01 |
#   |          |
#   |          |
#   |          |
#   |          |
#   |          |
#   |          |
#   |          |
#   ^----------^
#

import sys
sys.path.insert(0, "..")
import pyprofibus

def main(confdir=".", watchdog=None):
	master = None
	try:
		# Parse the config file.
		config = pyprofibus.PbConf.fromFile(confdir + "/example_asme01.conf")

		# Create a DP master.
		master = config.makeDPM()

		# Create the slave descriptions.
		outData = {}
		for slaveConf in config.slaveConfs:
			slaveDesc = slaveConf.makeDpSlaveDesc()

			# Set User_Prm_Data
			dp1PrmMask = bytearray((pyprofibus.dp.DpTelegram_SetPrm_Req.DPV1PRM0_FAILSAFE,
						pyprofibus.dp.DpTelegram_SetPrm_Req.DPV1PRM1_REDCFG,
						0x00))
			dp1PrmSet  = bytearray((pyprofibus.dp.DpTelegram_SetPrm_Req.DPV1PRM0_FAILSAFE,
						pyprofibus.dp.DpTelegram_SetPrm_Req.DPV1PRM1_REDCFG,
						0x00))
			slaveDesc.setUserPrmData(slaveConf.gsd.getUserPrmData(dp1PrmMask=dp1PrmMask,
									      dp1PrmSet=dp1PrmSet))

			# Register the AS ME-01 slave at the DPM
			master.addSlave(slaveDesc)

			# Set initial output data.
			outData[slaveDesc.name] = bytearray((0x00, 0x00))

		# Initialize the DPM
		master.initialize()

		# Cyclically run Data_Exchange.
		while True:
			# Write the output data.
			for slaveDesc in master.getSlaveList():
				slaveDesc.setMasterOutData(outData[slaveDesc.name])

			# Run slave state machines.
			handledSlaveDesc = master.run()

			# Get the in-data (receive)
			if handledSlaveDesc:
				inData = handledSlaveDesc.getMasterInData()
				if inData is not None:
					# In our example the output data shall be a mirror of the input.
					outData[handledSlaveDesc.name][0] = inData[0] & 3
					outData[handledSlaveDesc.name][1] = (inData[0] >> 2) & 3

			# Feed the system watchdog, if it is available.
			if watchdog is not None:
				watchdog()

	except pyprofibus.ProfibusError as e:
		print("Terminating: %s" % str(e))
		return 1
	finally:
		if master:
			master.destroy()
	return 0

if __name__ == "__main__":
	import sys
	sys.exit(main())
