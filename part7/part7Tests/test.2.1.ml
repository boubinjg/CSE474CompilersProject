begin
   int n;
   int s;
   int p;
   int i;
   i := 1;
   s := 0;
   p := 1;
   read(n);
   while i < n
   begin
      s := s + i;
      p := p * i;
      i := i + 1;
   end
   write(s, " ", p, " ");
end
