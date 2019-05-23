function baseplot(data)
   t = data.Times;
   rpm = data.s1rpm1;
   dc = data.s1dc1;
   plot(t, rpm, t, dc*1000)
end