function baseplot(data)
   t = data.Times;
   rpm = data.s1f1;
   dc = data.s1f22;
   plot(t, rpm, t, dc*1000)
end