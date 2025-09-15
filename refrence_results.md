Mandible:

# Manual Fusion: (Was 141.6mm too low)
TFM itk::simple::AffineTransform
 AffineTransform (000002BD94CAD340)
   RTTI typeinfo:   class itk::AffineTransform<double,3>
   Reference Count: 1
   Modified Time: 72898
   Debug: Off
   Object Name:
   Observers:
     none
   Matrix:
     1 0 0
     0 1 0
     0 0 1
   Offset: [-8, 206, -95]
   Center: [0, 0, 0]
   Translation: [-8, 206, -95]
   Inverse:
     1 0 0
     0 1 0
     0 0 1
   Singular: 0

# Auto Fusion (Was ~75mm too low)
TFM itk::simple::CompositeTransform
 CompositeTransform (00000199D7AA2B70)
   RTTI typeinfo:   class itk::CompositeTransform<double,3>
   Reference Count: 1
   Modified Time: 117173
   Debug: Off
   Object Name:
   Observers:
     none
   TransformQueue:
   >>>>>>>>>
   Euler3DTransform (00000198CDEB5460)
     RTTI typeinfo:   class itk::Euler3DTransform<double>
     Reference Count: 1
     Modified Time: 117160
     Debug: Off
     Object Name:
     Observers:
       none
     Matrix:
       1 0 0
       0 1 0
       0 0 1
     Offset: [7.0365, -204.838, -1.9]
     Center: [-7.0365, -0.1616, -367.1]
     Translation: [7.0365, -204.838, -1.9]
     Inverse:
       1 0 0
       0 1 0
       0 0 1
     Singular: 0
     AngleX: 0
     AngleY: 0
     AngleZ: 0
     ComputeZYX: Off
   >>>>>>>>>
   VersorRigid3DTransform (00000198CDEB3DB0)
     RTTI typeinfo:   class itk::VersorRigid3DTransform<double>
     Reference Count: 1
     Modified Time: 117169
     Debug: Off
     Object Name:
     Observers:
       none
     Matrix:
       0.997262 0.0269151 -0.0688739
       -0.0246453 0.999132 0.0335967
       0.0697183 -0.0318073 0.99706
     Offset: [-31.086, 12.6621, 34.4128]
     Center: [-7.0365, -0.1616, -367.1]
     Translation: [-5.78747, 0.50227, 35.0068]
     Inverse:
       0.997262 -0.0246453 0.0697183
       0.0269151 0.999132 -0.0318073
       -0.0688739 0.0335967 0.99706
     Singular: 0
     Versor: [ -0.0163644, -0.0346764, -0.0129007, 0.999181 ]
   TransformsToOptimizeFlags:
           0      1
   TransformsToOptimizeQueue:
   PreviousTransformsToOptimizeUpdateTime: 0