classdef FanRepr
   properties
      x0
      y0
      z0
      x1
      y1
      z1
      Z1
      Z0
      Y0
      Y1
      X0
      X1
      P
      c
      cmap
   end
   methods
       function obj = FanRepr(x, y, z, l, c)
            x0 = x; x1 = x + l;
            y0 = y; y1 = y + l;
            z0 = 0; z1 = z;
            C = [c c c c c];
            
            obj.P = cell(1, 5);
            obj.x0 = x0; obj.y0 = y0; obj.z0 = z0;
            obj.x1 = x1; obj.y1 = y1; obj.z1 = z1;
            
            obj.Z1 = patch([x0 x1 x1 x0 x0], [y0 y0 y1 y1 y0], [z1 z1 z1 z1 z1], C);  
            obj.Z0 = patch([x0 x1 x1 x0 x0], [y0 y0 y1 y1 y0], [z0 z0 z0 z0 z0], C);  
            
            
            obj.Y0 = patch([x0 x1 x1 x0 x0], [y0 y0 y0 y0 y0], [z0 z0 z1 z1 z0], C);
            obj.Y1 = patch([x0 x1 x1 x0 x0], [y1 y1 y1 y1 y1], [z0 z0 z1 z1 z0], C);
            
            obj.X0 = patch([x0 x0 x0 x0 x0], [y0 y0 y1 y1 y0], [z0 z1 z1 z0 z0], C);
            obj.X1 = patch([x1 x1 x1 x1 x1], [y0 y0 y1 y1 y0], [z0 z1 z1 z0 z0], C);
            
            obj.cmap = colormap;
       end
       function obj = setC(obj, C)
            obj.Z1.FaceColor = C; 
            obj.Z0.FaceColor = C;
            obj.Y0.FaceColor = C; 
            obj.Y1.FaceColor = C; 
            obj.X0.FaceColor = C; 
            obj.X1.FaceColor = C;
       end
       function obj = setz(obj, z)
%             x0 = obj.x0; y0 = obj.y0; z0 = obj.z0;
%             x1 = obj.x1; y1 = obj.y1; z1 = obj.z1;
%            
%             obj.Z1.Vertices = [obj.x0 obj.y0 z; obj.x1 obj.y1 z; obj.x1 obj.y0 z; obj.x0 obj.y0 0];
%             obj.Z0.Vertices = [obj.x0 obj.y0 0; obj.x1 obj.y1 0; obj.x1 obj.y0 0; obj.x0 obj.y0 0];
%             
%             obj.Y0.Vertices = [obj.x0 obj.y0 0; obj.x1 obj.y0 0; obj.x1 obj.y0 z; obj.x0 obj.y0 z];
%             obj.Y1.Vertices = [obj.x0 obj.y1 0; obj.x1 obj.y1 0; obj.x1 obj.y1 z; obj.x0 obj.y1 0];
%  
%             obj.X0.Vertices = [x0 x0 x0 x0 x0; y0 y0 y1 y1 y0; z0 z z z0 z0];
%             obj.X1.Vertices = [x1 x1 x1 x1 x1; y0 y0 y1 y1 y0; z0 z z z0 z0];

            Z = [z; z; z; z; z];
            Z_ = Z(3:4);
            
            obj.z1 = z;
            
            obj.Z1.Vertices(:,3) = Z;
            obj.Y0.Vertices(3:4, 3) = Z_;
            obj.Y1.Vertices(3:4, 3) = Z_;
            obj.X0.Vertices(2:3, 3) = Z_;
            obj.X1.Vertices(2:3, 3) = Z_;

       end
       function obj = set(obj, z, normd_val)
          obj.setz(z);
          obj.setC(obj.cmap(max([1 floor(normd_val*length(obj.cmap))]), :));
       end
   end
   
end