import viz
import math
import os, sys
from Vector3 import Vector3

#-------------------------------------------------------------------------------
# Low pass filter, used with low pass dynamic filter
#-------------------------------------------------------------------------------
class LowPassFilter:
	def __init__(self, cutoff):
		self.mFirstTime = True
		self.mCutoffFrequency = cutoff
		self.mPrevValue = Vector3(0,0,0)
		self.mTau = 0
		
	def SetCutoffFrequency(self,f): 
		self.mCutoffFrequency = f
		self.mTau = float(1.0 / (6.2831853 * self.mCutoffFrequency))	# a time constant calculated from the cut-off frequency

	def Apply(self, newValue, frequency):
		'''
		  Let's say Pnf the filtered position, Pn the non filtered position and Pn-1f the previous filtered position, 
		  Te the sampling period (in second) and tau a time constant calculated from the cut-off frequency fc.

		  tau = 1 / (2 * pi * fc)
		  Pnf = ( Pn + tau/Te * Pn-1f ) * 1/(1+ tau/Te)
		 
		  Attention: tau >= 10 * Te
		'''

		if self.mFirstTime:
			self.mPrevValue = Vector3(newValue)
			self.mFirstTime = False
		
		Te = float(1.0 / float(frequency))		# the sampling period (in seconds)

		filteredValue = (newValue + self.mPrevValue * (self.mTau/Te)) * (1.0 / (1.0 + self.mTau/Te))

		# filter position and velocity at the same 
		self.mPrevValue = Vector3(filteredValue)
		return filteredValue

	def Clear(self):
		self.mFirstTime = True

#-------------------------------------------------------------------------------
#Low pass dynamic filter, used to smooth the cursor.
#-------------------------------------------------------------------------------
class LowPassDynamicFilter(LowPassFilter):
	def __init__(self,cutoffLow=0, cutoffHigh=0, velocityLow=0, velocityHigh=0):
		LowPassFilter.__init__(self,cutoffLow)
		
		self.mVelocityFilter = LowPassFilter(cutoffLow)
		self.mFirstTime = True
		self.mCutoffFrequencyHigh = cutoffHigh 
		self.mVelocityLow = velocityLow
		self.mVelocityHigh = velocityHigh 
		self.SetCutoffFrequencyVelocity()
		self.mLastPositionForVelocity = 0.0
		
	def SetCutoffFrequencyVelocity(self) :
		self.mVelocityFilter.SetCutoffFrequency(float(self.mCutoffFrequency  + 0.75 * (self.mCutoffFrequencyHigh - self.mCutoffFrequency)))

	def Apply(self, NewValue, frequency):
		# special case if first time being used
		if self.mFirstTime:
			self.mPrevValue = Vector3(NewValue)
			self.mLastPositionForVelocity = Vector3(NewValue)
			self.mFirstTime = False
		
		# first get an estimate of velocity (with filter)
		self.mPositionForVelocity = self.mVelocityFilter.Apply(NewValue, frequency)
		vel = (self.mPositionForVelocity - self.mLastPositionForVelocity) * frequency
		self.mLastPositionForVelocity = Vector3(self.mPositionForVelocity)
		vel = vel.abs()
		
		# interpolate between frequencies depending on velocity
		t = (vel - Vector3(self.mVelocityLow, self.mVelocityLow, self.mVelocityLow)) / (self.mVelocityHigh - self.mVelocityLow)

		t = t.max(0.0)
		t = t.min(1.0)

		cutoff = (Vector3(t.x,t.y,t.z) * self.mCutoffFrequencyHigh) + ((Vector3(1,1,1) - Vector3(t.x,t.y,t.z)) * self.mCutoffFrequency)

		Te = Vector3(1.0 / frequency, 1.0 / frequency, 1.0 / frequency)		# the sampling period (in seconds)
		Tau = Vector3(1.0 / (6.2831853 * cutoff.x), 1.0 / (6.2831853 * cutoff.y), 1.0 / (6.2831853 * cutoff.z))	# a time constant calculated from the cut-off frequency

		filteredValue = Vector3
		filteredValue.x = (NewValue.x + (Tau.x / Te.x) * self.mPrevValue.x) * (1.0 / (1.0 + Tau.x / Te.x))
		filteredValue.y = (NewValue.y + (Tau.y / Te.y) * self.mPrevValue.y) * (1.0 / (1.0 + Tau.y / Te.y))
		filteredValue.z = (NewValue.z + (Tau.z / Te.z) * self.mPrevValue.z) * (1.0 / (1.0 + Tau.z / Te.z))

		self.mPrevValue = Vector3(filteredValue)
		
		return filteredValue

