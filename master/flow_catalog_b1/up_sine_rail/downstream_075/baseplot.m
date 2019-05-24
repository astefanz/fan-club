function baseplot(data)
   t = data.Times;
   rpm = data.s1rpm13;
   dc = data.s1dc13;
   plot(t, rpm, t, dc*1000)
end