%!PS-Adobe-2.0
%%Creator: Terry Burton
%%DocumentPaperSizes: a4
%%EndComments
%%EndProlog

% Barcode Writer in Pure PostScript - Version 2008-07-10
% http://www.terryburton.co.uk/barcodewriter/
%
% Copyright (c) 2008 Terry Burton - tez@terryburton.co.uk
%
% Permission is hereby granted, free of charge, to any
% person obtaining a copy of this software and associated
% documentation files (the "Software"), to deal in the
% Software without restriction, including without
% limitation the rights to use, copy, modify, merge,
% publish, distribute, sublicense, and/or sell copies of
% the Software, and to permit persons to whom the Software
% is furnished to do so, subject to the following
% conditions:
%
% The above copyright notice and this permission notice
% shall be included in all copies or substantial portions
% of the Software.
%
% THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
% KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
% THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
% PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
% THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
% DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
% CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
% CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
% IN THE SOFTWARE.

% Uncomment this next line to allow these procedure definitions to 
% remain resident within a printer's PostScript virtual machine 
% so that the barcode generation capability persists between jobs.

% serverdict begin 0 exitserver 

% --BEGIN TEMPLATE--

% --BEGIN ENCODER ean13--
% --DESC: EAN-13
% --EXAM: 977147396801
% --EXOP: includetext guardwhitespace
% --RNDR: renlinear
/ean13 {

    0 begin

    /options exch def                  % We are given an option string
    /useropts options def
    /barcode exch def                  % We are given a barcode string

    /includetext false def             % Enable/disable text
    /textfont /Helvetica def
    /textsize 12 def
    /textyoffset -4 def
    /height 1 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /textyoffset textyoffset cvr def
    /height height cvr def
    
    /barlen barcode length def         % Length of the code

    % Add checksum digit to barcode if length is even
    barlen 2 mod 0 eq {
        /pad barlen 1 add string def   % Create pad one bigger than barcode
        /checksum 0 def
        0 1 barlen 1 sub {
            /i exch def
            /barchar barcode i get 48 sub def
            i 2 mod 0 eq {
                /checksum barchar checksum add def
            } {
                /checksum barchar 3 mul checksum add def
            } ifelse
        } for
        /checksum 10 checksum 10 mod sub 10 mod def
        pad 0 barcode putinterval       % Add barcode to the start of the pad
        pad barlen checksum 48 add put  % Put ascii for checksum at end of pad
        /barcode pad def                % barcode=pad
        /barlen barlen 1 add def        % barlen++
    } if

    % Create an array containing the character mappings
    /encs
    [ (3211) (2221) (2122) (1411) (1132)
      (1231) (1114) (1312) (1213) (3112)
      (111) (11111) (111)
    ] def

    % Create a string of the available characters
    /barchars (0123456789) def

    % Digits to mirror on left side
    /mirrormaps
    [ (000000) (001011) (001101) (001110) (010011)
      (011001) (011100) (010101) (010110) (011010)
    ] def

    /sbs barlen 1 sub 4 mul 11 add string def
    /txt barlen array def
  
    % Put the start character
    sbs 0 encs 10 get putinterval

    % First digit - determine mirrormap by this and show before guard bars
    /mirrormap mirrormaps barcode 0 get 48 sub get def
    txt 0 [barcode 0 1 getinterval -10 textyoffset textfont textsize] put

    % Left side - performs mirroring
    1 1 6 {
        % Lookup the encoding for the each barcode character
        /i exch def
        barcode i 1 getinterval barchars exch search
        pop                            % Discard true leaving pre
        length /indx exch def          % indx is the length of pre
        pop pop                        % Discard seek and post
        /enc encs indx get def         % Get the indxth encoding
        mirrormap i 1 sub get 49 eq {   % Reverse enc if 1 in this position in mirrormap
            /enclen enc length def
            /revenc enclen string def
            0 1 enclen 1 sub {
                /j exch def
                /char enc j get def
                revenc enclen j sub 1 sub char put
            } for
            /enc revenc def
        } if
        sbs i 1 sub 4 mul 3 add enc putinterval   % Put encoded digit into sbs
        txt i [barcode i 1 getinterval i 1 sub 7 mul 4 add textyoffset textfont textsize] put
    } for

    % Put the middle character
    sbs 7 1 sub 4 mul 3 add encs 11 get putinterval

    % Right side
    7 1 12 {
        % Lookup the encoding for the each barcode character
        /i exch def
        barcode i 1 getinterval barchars exch search
        pop                            % Discard true leaving pre
        length /indx exch def          % indx is the length of pre
        pop pop                        % Discard seek and post
        /enc encs indx get def         % Get the indxth encoding
        sbs i 1 sub 4 mul 8 add enc putinterval  % Put encoded digit into sbs
        txt i [barcode i 1 getinterval i 1 sub 7 mul 8 add textyoffset textfont textsize] put
    } for

    % Put the end character
    sbs barlen 1 sub 4 mul 8 add encs 12 get putinterval
    
    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) [sbs {48 sub} forall] put
    includetext {
        retval (bhs) [height height 12{height .075 sub}repeat height height 12{height .075 sub}repeat height height] put
        retval (bbs) [0 0 12{.075}repeat 0 0 12{.075}repeat 0 0] put
        retval (txt) txt put
    } {
        retval (bhs) [30{height}repeat] put        
        retval (bbs) [30{0}repeat] put
    } ifelse
    retval (opt) useropts put
    retval (guardrightpos) 10 put
    retval (borderbottom) 5 put
    retval
    
    end

} bind def
/ean13 load 0 1 dict put
% --END ENCODER ean13--

% --BEGIN ENCODER ean8--
% --DESC: EAN-8
% --EXAM: 01335583
% --EXOP: includetext guardwhitespace height=0.5
% --RNDR: renlinear
/ean8 {

    0 begin

    /options exch def                  % We are given an option string
    /useropts options def
    /barcode exch def                  % We are given a barcode string

    /includetext false def              % Enable/disable text
    /textfont /Helvetica def
    /textsize 12 def
    /textyoffset -4 def
    /height 1 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /textyoffset textyoffset cvr def
    /height height cvr def
    
    % Create an array containing the character mappings
    /encs
    [ (3211) (2221) (2122) (1411) (1132)
      (1231) (1114) (1312) (1213) (3112)
      (111) (11111) (111)
    ] def

    % Create a string of the available characters
    /barchars (0123456789) def

    /barlen barcode length def           % Length of the code
    /sbs barlen 4 mul 11 add string def
    /txt barlen array def
    
    % Put the start character
    sbs 0 encs 10 get putinterval

    % Left side
    0 1 3 {
        % Lookup the encoding for the each barcode character
        /i exch def
        barcode i 1 getinterval barchars exch search
        pop                                % Discard true leaving pre
        length /indx exch def              % indx is the length of pre
        pop pop                            % Discard seek and post
        /enc encs indx get def             % Get the indxth encoding
        sbs i 4 mul 3 add enc putinterval  % Put encoded digit into sbs
        txt i [barcode i 1 getinterval i 7 mul 4 add textyoffset textfont textsize] put
    } for

    % Put the middle character
    sbs 4 4 mul 3 add encs 11 get putinterval

    % Right side
    4 1 7 {
        % Lookup the encoding for the each barcode character
        /i exch def
        barcode i 1 getinterval barchars exch search
        pop                                % Discard true leaving pre
        length /indx exch def              % indx is the length of pre
        pop pop                            % Discard seek and post
        /enc encs indx get def             % Get the indxth encoding
        sbs i 4 mul 8 add enc putinterval  % Put encoded digit into sbs
        txt i [barcode i 1 getinterval i 7 mul 8 add textyoffset textfont textsize] put
    } for

    % Put the end character
    sbs barlen 4 mul 8 add encs 12 get putinterval

    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) [sbs {48 sub} forall] put
    includetext {
        retval (bhs) [height height 8{height .075 sub}repeat height height 8{height .075 sub}repeat height height] put
        retval (bbs) [0 0 8{.075}repeat 0 0 8{.075}repeat 0 0] put
        retval (txt) txt put
    } {
        retval (bhs) [22{height}repeat] put        
        retval (bbs) [22{0}repeat] put
    } ifelse
    retval (opt) useropts put
    retval (guardleftpos) 10 put
    retval (guardrightpos) 10 put
    retval (borderbottom) 5 put
    retval

    end

} bind def
/ean8 load 0 1 dict put
% --END ENCODER ean8--

% --BEGIN ENCODER upca--
% --DESC: UPC-A
% --EXAM: 78858101497
% --EXOP: includetext
% --RNDR: renlinear
/upca {

    0 begin

    /options exch def
    /useropts options def
    /barcode exch def             % We are given a barcode string

    /includetext false def         % Enable/disable text
    /textfont /Helvetica def
    /textsize 12 def
    /textyoffset -4 def
    /height 1 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /textyoffset textyoffset cvr def
    /height height cvr def
    
    /barlen barcode length def         % Length of the code

    % Add checksum digit to barcode if length is odd
    barlen 2 mod 0 ne {
        /pad barlen 1 add string def   % Create pad one bigger than barcode
        /checksum 0 def
        0 1 barlen 1 sub {
           /i exch def
           /barchar barcode i get 48 sub def
           i 2 mod 0 ne {
               /checksum checksum barchar add def
           } {
               /checksum checksum barchar 3 mul add def
           } ifelse
        } for
        /checksum 10 checksum 10 mod sub 10 mod def
        pad 0 barcode putinterval       % Add barcode to the start of the pad
        pad barlen checksum 48 add put  % Put ascii for checksum at end of pad
        /barcode pad def                % barcode=pad
        /barlen barlen 1 add def        % barlen++
    } if

    % Create an array containing the character mappings
    /encs
    [ (3211) (2221) (2122) (1411) (1132)
      (1231) (1114) (1312) (1213) (3112)
      (111) (11111) (111)
    ] def

    % Create a string of the available characters
    /barchars (0123456789) def

    /sbs barlen 4 mul 11 add string def
    /txt barlen array def

    % Put the start character
    sbs 0 encs 10 get putinterval

    % Left side
    0 1 5 {
        % Lookup the encoding for the each barcode character
        /i exch def
        barcode i 1 getinterval barchars exch search
        pop                                % Discard true leaving pre
        length /indx exch def              % indx is the length of pre
        pop pop                            % Discard seek and post
        /enc encs indx get def             % Get the indxth encoding
        sbs i 4 mul 3 add enc putinterval  % Put encoded digit into sbs
        i 0 eq {      % First digit is before the guard bars
            txt 0 [barcode 0 1 getinterval -7 textyoffset textfont textsize 2 sub] put
        } {
            txt i [barcode i 1 getinterval i 7 mul 4 add textyoffset textfont textsize] put
        } ifelse
    } for

    % Put the middle character
    sbs 6 4 mul 3 add encs 11 get putinterval

    % Right side
    6 1 11 {
        % Lookup the encoding for the each barcode character
        /i exch def
        barcode i 1 getinterval barchars exch search
        pop                                % Discard true leaving pre
        length /indx exch def              % indx is the length of pre
        pop pop                            % Discard seek and post
        /enc encs indx get def             % Get the indxth encoding
        sbs i 4 mul 8 add enc putinterval  % Put encoded digit into sbs
        i 11 eq {       % Last digit is after guard bars
            txt 11 [barcode 11 1 getinterval 96 textyoffset textfont textsize 2 sub] put
        } {
            txt i [barcode i 1 getinterval i 7 mul 8 add textyoffset textfont textsize] put
        } ifelse
    } for

    % Put the end character
    sbs barlen 4 mul 8 add encs 12 get putinterval

    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) [sbs {48 sub} forall] put
    includetext {
        retval (bhs) [4{height}repeat 10{height .075 sub}repeat height height 10{height .075 sub}repeat 5{height}repeat] put      
        retval (bbs) [0 0 0 0 10{.075}repeat 0 0 10{.075}repeat 0 0 0 0 0] put
        retval (txt) txt put
    } {
        retval (bhs) [31{height}repeat] put
        retval (bbs) [31{0}repeat] put
    } ifelse
    retval (opt) useropts put
    retval (borderbottom) 5 put
    retval

    end

} bind def
/upca load 0 1 dict put
% --END ENCODER upca--

% --BEGIN ENCODER upce--
% --DESC: UPC-E
% --EXAM: 0123456
% --EXOP: includetext height=0.4
% --RNDR: renlinear
/upce {

    0 begin

    /options exch def                   % We are given an option string
    /useropts options def
    /barcode exch def                   % We are given a barcode string

    /includetext false def               % Enable/disable text
    /textfont /Helvetica def
    /textsize 12 def
    /textyoffset -4 def
    /height 1 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /textyoffset textyoffset cvr def
    /height height cvr def
    
    /barlen barcode length def          % Length of the code

    % Create an array containing the character mappings
    /encs
    [ (3211) (2221) (2122) (1411) (1132)
      (1231) (1114) (1312) (1213) (3112)
      (111) (1111111)
    ] def

    % Create a string of the available characters
    /barchars (0123456789) def

    /mirrormaps
    [ (000111) (001011) (001101) (001110) (010011)
      (011001) (011100) (010101) (010110) (011010)
    ] def

    % Add checksum digit to barcode if length is odd
    barlen 2 mod 0 ne {
        % Derive the equivalent UPC-A for its checksum
        /upcacode (00000000000) 11 string copy def
        barcode 6 get 48 sub 2 le {
            upcacode 1 barcode 1 2 getinterval putinterval
            upcacode 3 barcode 6 1 getinterval putinterval
            upcacode 8 barcode 3 3 getinterval putinterval
        } if
        barcode 6 get 48 sub 3 eq {
            upcacode 1 barcode 1 3 getinterval putinterval
            upcacode 9 barcode 4 2 getinterval putinterval
        } if
        barcode 6 get 48 sub 4 eq {
            upcacode 1 barcode 1 4 getinterval putinterval
            upcacode 10 barcode 5 1 getinterval putinterval
        } if
        barcode 6 get 48 sub 5 ge {
            upcacode 1 barcode 1 5 getinterval putinterval
            upcacode 10 barcode 6 1 getinterval putinterval
        } if
        /checksum 0 def
        0 1 10 {
           /i exch def
           /barchar upcacode i get 48 sub def
           i 2 mod 0 ne {
               /checksum checksum barchar add def
           } {
               /checksum checksum barchar 3 mul add def
           } ifelse
        } for
        /checksum 10 checksum 10 mod sub 10 mod def
        /pad barlen 1 add string def    % Create pad one bigger than barcode
        pad 0 barcode putinterval       % Add barcode to the start of the pad
        pad barlen checksum 48 add put  % Put ascii for checksum at end of pad
        /barcode pad def                % barcode=pad
        /barlen barlen 1 add def        % barlen++
    } if
    /txt barlen array def
    txt 0 [barcode 0 1 getinterval -7 textyoffset textfont textsize 2 sub] put

    % Determine the mirror map based on checksum
    /mirrormap mirrormaps barcode barlen 1 sub get 48 sub get def

    % Invert the mirrormap if we are using a non-zero number system
    barcode 0 get 48 eq {
        /invt mirrormap length string def
        0 1 mirrormap length 1 sub {
            /i exch def
            mirrormap i get 48 eq {
                invt i 49 put
            } {
                invt i 48 put
            } ifelse
        } for
        /mirrormap invt def
    } if

    /sbs barlen 2 sub 4 mul 10 add string def

    % Put the start character
    sbs 0 encs 10 get putinterval

    1 1 6 {
        /i exch def
        % Lookup the encoding for the each barcode character
        barcode i 1 getinterval barchars exch search
        pop                            % Discard true leaving pre
        length /indx exch def          % indx is the length of pre
        pop pop                        % Discard seek and post
        /enc encs indx get def         % Get the indxth encoding
        mirrormap i 1 sub get 49 eq {  % Reverse enc if 1 in this position in mirrormap        
            /enclen enc length def
            /revenc enclen string def
            0 1 enclen 1 sub {
                /j exch def
                /char enc j get def
                revenc enclen j sub 1 sub char put
            } for
            /enc revenc def
        } if
        sbs i 1 sub 4 mul 3 add enc putinterval   % Put encoded digit into sbs
        txt i [barcode i 1 getinterval i 1 sub 7 mul 4 add textyoffset textfont textsize] put
    } for

    txt 7 [barcode 7 1 getinterval 6 7 mul 11 add textyoffset textfont textsize 2 sub] put

    % Put the end character
    sbs barlen 2 sub 4 mul 3 add encs 11 get putinterval

    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) [sbs {48 sub} forall] put
    includetext {
        retval (bhs) [height height 12{height .075 sub}repeat height height height] put      
        retval (bbs) [0 0 12{.075}repeat 0 0 0] put    
        retval (txt) txt put
    } {
        retval (bhs) [17{height}repeat] put      
        retval (bbs) [17{0}repeat] put    
    } ifelse
    retval (opt) useropts put
    retval (borderbottom) 5 put
    retval

    end

} bind def
/upce load 0 1 dict put
% --END ENCODER upce--

% --BEGIN ENCODER ean5--
% --DESC: EAN-5 (5 digit addon)
% --EXAM: 90200
% --EXOP: includetext guardwhitespace
% --RNDR: renlinear
/ean5 {

    0 begin

    /options exch def                   % We are given an option string
    /useropts options def
    /barcode exch def                   % We are given a barcode string

    /includetext false def              % Enable/disable text
    /textfont /Helvetica def
    /textsize 12 def
    /textyoffset (unset) def
    /height 0.7 def    
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /height height cvr def
    textyoffset (unset) eq {
        /textyoffset height 72 mul 1 add def
    } {
        /textyoffset textyoffset cvr def
    } ifelse
    
    /barlen barcode length def          % Length of the code

    % Create an array containing the character mappings
    /encs
    [ (3211) (2221) (2122) (1411) (1132)
      (1231) (1114) (1312) (1213) (3112)
      (112) (11)
    ] def

    % Create a string of the available characters
    /barchars (0123456789) def

    % Determine the mirror map based on mod 10 checksum
    /mirrormaps
    [ (11000) (10100) (10010) (10001) (01100)
      (00110) (00011) (01010) (01001) (00101)
    ] def
    /checksum 0 def
    0 1 4 {
        /i exch def
        /barchar barcode i get 48 sub def
        i 2 mod 0 eq {
            /checksum barchar 3 mul checksum add def
        } {
            /checksum barchar 9 mul checksum add def
        } ifelse
    } for
    /checksum checksum 10 mod def
    /mirrormap mirrormaps checksum get def

    /sbs 31 string def
    /txt 5 array def
   
    0 1 4 {
        /i exch def

        % Prefix with either a start character or separator character
        i 0 eq {
            sbs 0 encs 10 get putinterval
        } {
            sbs i 1 sub 6 mul 7 add encs 11 get putinterval
        } ifelse

        % Lookup the encoding for the barcode character
        barcode i 1 getinterval barchars exch search
        pop                     % Discard true leaving pre
        length /indx exch def   % indx is the length of pre
        pop pop                 % Discard seek and post
        /enc encs indx get def  % Get the indxth encoding
        mirrormap i get 49 eq { % Reverse enc if 1 in this position in mirrormap
            /enclen enc length def
            /revenc enclen string def
            0 1 enclen 1 sub {
                /j exch def
                /char enc j get def
                revenc enclen j sub 1 sub char put
            } for
            /enc revenc def
        } if
        sbs i 6 mul 3 add enc putinterval   % Put encoded digit into sbs
        txt i [barcode i 1 getinterval i 1 sub 9 mul 13 add textyoffset textfont textsize] put
    } for

    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) [sbs {48 sub} forall] put
    retval (bhs) [16{height}repeat] put
    retval (bbs) [16{0}repeat] put
    includetext {
        retval (txt) txt put
    } if
    retval (opt) useropts put
    retval (guardrightpos) 10 put
    retval (guardrightypos) textyoffset 4 add put
    retval (bordertop) 10 put
    retval

    end

} bind def
/ean5 load 0 1 dict put
% --END ENCODER ean5--

% --BEGIN ENCODER ean2--
% --DESC: EAN-2 (2 digit addon)
% --EXAM: 05
% --EXOP: includetext guardwhitespace
% --RNDR: renlinear
/ean2 {

    0 begin

    /options exch def                   % We are given an options string
    /useropts options def
    /barcode exch def                   % We are given a barcode string

    /includetext false def               % Enable/disable text
    /textfont /Helvetica def
    /textsize 12 def
    /textyoffset (unset) def
    /height 0.7 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /height height cvr def
    textyoffset (unset) eq {
        /textyoffset height 72 mul 1 add def
    } {
        /textyoffset textyoffset cvr def
    } ifelse
    
    /barlen barcode length def          % Length of the code

    % Create an array containing the character mappings
    /encs
    [ (3211) (2221) (2122) (1411) (1132)
      (1231) (1114) (1312) (1213) (3112)
      (112) (11)
    ] def

    % Create a string of the available characters
    /barchars (0123456789) def

    % Determine the mirror map based on mod 4 checksum
    /mirrormap [(00) (01) (10) (11)] barcode 0 2 getinterval cvi 4 mod get def

    /sbs 13 string def
    /txt 2 array def
    
    0 1 1 {
        /i exch def

        % Prefix with either a start character or separator character
        i 0 eq {
            sbs 0 encs 10 get putinterval
        } {
            sbs i 1 sub 6 mul 7 add encs 11 get putinterval
        } ifelse

        % Lookup the encoding for the barcode character
        barcode i 1 getinterval barchars exch search
        pop                     % Discard true leaving pre
        length /indx exch def   % indx is the length of pre
        pop pop                 % Discard seek and post
        /enc encs indx get def  % Get the indxth encoding
        mirrormap i get 49 eq { % Reverse enc if 1 in this position in mirrormap    
            /enclen enc length def
            /revenc enclen string def
            0 1 enclen 1 sub {
                /j exch def
                /char enc j get def
                revenc enclen j sub 1 sub char put
            } for
            /enc revenc def
        } if
        sbs i 6 mul 3 add enc putinterval   % Put encoded digit into sbs
        txt i [barcode i 1 getinterval i 1 sub 9 mul 13 add textyoffset textfont textsize] put
    } for

    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) [sbs {48 sub} forall] put
    retval (bhs) [12{height}repeat] put
    retval (bbs) [12{0}repeat] put
    includetext {
        retval (txt) txt put
    } if
    retval (opt) useropts put
    retval (guardrightpos) 10 put
    retval (guardrightypos) textyoffset 4 add put
    retval (bordertop) 10 put
    retval

    end

} bind def
/ean2 load 0 1 dict put
% --END ENCODER ean2--

% --BEGIN ENCODER isbn--
% --REQUIRES ean13--
% --DESC: ISBN
% --EXAM: 978-1-56592-479
% --EXOP: includetext guardwhitespace
% --RNDR: renlinear
/isbn {

    0 begin

    /options exch def      % We are given an options string
    /useropts options def
    /isbntxt exch def      % We are given the isbn text with dashes

    /includetext false def  % Enable/disable ISBN text
    /isbnfont /Courier def
    /isbnsize 9 def
    /isbnpos (unset) def
    /height 1 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /isbnfont isbnfont cvlit def
    /isbnsize isbnsize cvr def
    /height height cvr def
    isbnpos (unset) eq {
        /isbnpos height 72 mul 3 add def
    } {
        /isbnpos isbnpos cvr def
    } ifelse
    
    % Read the digits from isbntxt and calculate checksums
    /isbn 13 string def
    /checksum10 0 def
    /checksum13 0 def
    /i 0 def /n 0 def
    { % loop
        /isbnchar isbntxt i get 48 sub def
        isbnchar -3 ne {     % Ignore dashes
            isbn n isbnchar 48 add put
            /checksum10 checksum10 10 n sub isbnchar mul add def
            n 2 mod 0 eq {
                /checksum13 isbnchar checksum13 add def
            } {
                /checksum13 isbnchar 3 mul checksum13 add def
            } ifelse
            /n n 1 add def
        } if
        /i i 1 add def
        i isbntxt length eq {exit} if
    } loop

    % Add the ISBN header to the isbntxt
    n 9 eq n 10 eq or {
        /checksum 11 checksum10 11 mod sub 11 mod def
        /isbn isbn 0 9 getinterval def
        /pad 18 string def
    } {
        /checksum 10 checksum13 10 mod sub 10 mod def
        /isbn isbn 0 12 getinterval def
        /pad 22 string def
    } ifelse
    pad 0 (ISBN ) putinterval
    pad 5 isbntxt putinterval  % Add isbntxt to the pad

    % Add checksum digit if isbntxt length is 11 or 15
    isbntxt length 11 eq isbntxt length 12 eq or 
    isbntxt length 15 eq or isbntxt length 16 eq or {
        pad pad length 2 sub 45 put  % Put a dash
        checksum 10 eq {
            pad pad length 1 sub checksum 78 add put  % Check digit for 10 is X
        } {
            pad pad length 1 sub checksum 48 add put  % Put check digit
        } ifelse
    } if
    /isbntxt pad def                    % isbntxt=pad

    % Convert ISBN digits to EAN-13
    /barcode 12 string def
    isbn length 9 eq {        
        barcode 0 (978) putinterval
        barcode 3 isbn putinterval
    } {
        barcode 0 isbn putinterval
    } ifelse

    % Get the result of encoding with ean13    
    /args barcode options ean13 def

    % Add the ISBN text
    includetext {
        isbn length 9 eq {
            /isbnxpos -1 def
        } {
            /isbnxpos -12 def
        } ifelse
        args (txt) known {
            /txt args (txt) get def
            /newtxt txt length 1 add array def
            newtxt 0 txt putinterval
            newtxt newtxt length 1 sub [isbntxt isbnxpos isbnpos isbnfont isbnsize] put
            args (txt) newtxt put
        } {
            args (txt) [ [isbntxt isbnxpos isbnpos isbnfont isbnsize] ] put
        } ifelse
    } if

    args (opt) useropts put
    args

    end
 
} bind def
/isbn load 0 1 dict put
% --END ENCODER isbn--

% --BEGIN ENCODER code128--
% --DESC: Code 128
% --EXAM: ^104^102Count^0990123456789^101!
% --EXOP: includetext
% --RNDR: renlinear
/code128 {

    0 begin                  % Confine variables to local scope

    /options exch def        % We are given an option string
    /useropts options def
    /barcode exch def        % We are given a barcode string

    /includetext false def    % Enable/disable text
    /textfont /Courier def
    /textsize 10 def
    /textyoffset -7 def
    /height 1 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /textyoffset textyoffset cvr def
    /height height cvr def
    
    % Create an array containing the character mappings
    /encs
    [ (212222) (222122) (222221) (121223) (121322) (131222) (122213)
      (122312) (132212) (221213) (221312) (231212) (112232) (122132)
      (122231) (113222) (123122) (123221) (223211) (221132) (221231)
      (213212) (223112) (312131) (311222) (321122) (321221) (312212)
      (322112) (322211) (212123) (212321) (232121) (111323) (131123)
      (131321) (112313) (132113) (132311) (211313) (231113) (231311)
      (112133) (112331) (132131) (113123) (113321) (133121) (313121)
      (211331) (231131) (213113) (213311) (213131) (311123) (311321)
      (331121) (312113) (312311) (332111) (314111) (221411) (431111)
      (111224) (111422) (121124) (121421) (141122) (141221) (112214)
      (112412) (122114) (122411) (142112) (142211) (241211) (221114)
      (413111) (241112) (134111) (111242) (121142) (121241) (114212)
      (124112) (124211) (411212) (421112) (421211) (212141) (214121)
      (412121) (111143) (111341) (131141) (114113) (114311) (411113)
      (411311) (113141) (114131) (311141) (411131) (211412) (211214)
      (211232) (2331112)
    ] def

    % Create a string of the available characters for alphabets A and B
    /barchars ( !"#$%&'\(\)*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~) def
    /barlen barcode length def    % Length of the code
    /sbs barlen 6 mul string def  % sbs is 6 times length of barcode
    /txt barlen array def

    /mode -1 def         % A=0, B=1, C=2
    /checksum barcode 1 3 getinterval cvi def  % Initialise the checksum

    /i 0 def /j 0 def
    { % loop
        i barlen eq {exit} if
        barcode i 1 getinterval (^) eq {
            % indx is given by the next three characters
            /indx barcode i 1 add 3 getinterval cvi def
            txt j [( ) j 11 mul textyoffset textfont textsize] put
            /i i 4 add def
        } {
            % indx depends on the mode
            mode 2 eq {
                /indx barcode i 2 getinterval cvi def
                txt j [barcode i 2 getinterval j 11 mul textyoffset textfont textsize] put
                /i i 2 add def
            } {
                barchars barcode i 1 getinterval search
                pop                    % Discard true leaving pre
                length /indx exch def  % indx is the length of pre
                pop pop                % Discard seek and post
                txt j [barchars indx 1 getinterval j 11 mul textyoffset textfont textsize] put
                /i i 1 add def
            } ifelse
        } ifelse
        /enc encs indx get def         % Get the indxth encoding
        sbs j 6 mul enc putinterval    % Put encoded digit into sbs

        % Update the mode
        indx 101 eq indx 103 eq or {/mode 0 def} if
        indx 100 eq indx 104 eq or {/mode 1 def} if
        indx 99 eq indx 105 eq or {/mode 2 def} if

        /checksum indx j mul checksum add def  % checksum+=indx*j
        /j j 1 add def
    } loop

    % Put the checksum character
    /checksum checksum 103 mod def
    sbs j 6 mul encs checksum get putinterval

    % Put the end character
    sbs j 6 mul 6 add encs 106 get putinterval

    % Shrink sbs and txt to fit exactly
    /sbs sbs 0 j 6 mul 13 add getinterval def
    /txt txt 0 j getinterval def

    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) [sbs {48 sub} forall] put
    retval (bhs) [sbs length 1 add 2 idiv {height} repeat] put
    retval (bbs) [sbs length 1 add 2 idiv {0} repeat] put
    includetext {
        retval (txt) txt put
    } if
    retval (opt) useropts put
    retval

    end

} bind def
/code128 load 0 1 dict put
% --END ENCODER code128--

% --BEGIN ENCODER code39--
% --DESC: Code 39
% --EXAM: THIS IS CODE 39
% --EXOP: includetext includecheck includecheckintext
% --RNDR: renlinear
/code39 {

    0 begin                 % Confine variables to local scope

    /options exch def       % We are given an option string
    /useropts options def
    /barcode exch def       % We are given a barcode string

    /includecheck false def  % Enable/disable checkdigit
    /includetext false def
    /includecheckintext false def
    /textfont /Courier def
    /textsize 10 def
    /textyoffset -7 def
    /height 1 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /textyoffset textyoffset cvr def
    /height height cvr def
    
    % Create an array containing the character mappings
    /encs
    [ (1113313111) (3113111131) (1133111131) (3133111111) (1113311131)
      (3113311111) (1133311111) (1113113131) (3113113111) (1133113111)
      (3111131131) (1131131131) (3131131111) (1111331131) (3111331111)
      (1131331111) (1111133131) (3111133111) (1131133111) (1111333111)
      (3111111331) (1131111331) (3131111311) (1111311331) (3111311311)
      (1131311311) (1111113331) (3111113311) (1131113311) (1111313311)
      (3311111131) (1331111131) (3331111111) (1311311131) (3311311111)
      (1331311111) (1311113131) (3311113111) (1331113111) (1313131111)
      (1313111311) (1311131311) (1113131311) (1311313111)
    ] def

    % Create a string of the available characters
    /barchars (0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%*) def

    /barlen barcode length def  % Length of the code

    includecheck {
        /sbs barlen 10 mul 30 add string def
        /txt barlen 3 add array def
    } {
        /sbs barlen 10 mul 20 add string def
        /txt barlen 2 add array def
    } ifelse

    /checksum 0 def

    % Put the start character
    sbs 0 encs 43 get putinterval
    txt 0 [(*) 0 textyoffset textfont textsize] put

    0 1 barlen 1 sub {
        /i exch def
        % Lookup the encoding for the each barcode character
        barcode i 1 getinterval barchars exch search
        pop                                  % Discard true leaving pre
        length /indx exch def                % indx is the length of pre
        pop pop                              % Discard seek and post
        /enc encs indx get def               % Get the indxth encoding
        sbs i 10 mul 10 add enc putinterval  % Put encoded digit into sbs
        txt i 1 add [barcode i 1 getinterval i 1 add 16 mul textyoffset textfont textsize] put
        /checksum checksum indx add def
    } for

    % Put the checksum and end characters
    includecheck {
        /checksum checksum 43 mod def
        sbs barlen 10 mul 10 add encs checksum get putinterval
        includecheckintext {
            txt barlen 1 add [barchars checksum 1 getinterval barlen 1 add 16 mul textyoffset textfont textsize] put
        } {
            txt barlen 1 add [() barlen 1 add 16 mul textyoffset textfont textsize] put
        } ifelse
        sbs barlen 10 mul 20 add encs 43 get putinterval
        txt barlen 2 add [(*) barlen 2 add 16 mul textyoffset textfont textsize] put
    } {
        sbs barlen 10 mul 10 add encs 43 get putinterval
        txt barlen 1 add [(*) barlen 1 add 16 mul textyoffset textfont textsize] put
    } ifelse
    
    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) [sbs {48 sub} forall] put
    retval (bhs) [sbs length 1 add 2 idiv {height} repeat] put
    retval (bbs) [sbs length 1 add 2 idiv {0} repeat] put
    includetext {
        retval (txt) txt put
    } if
    retval (opt) useropts put
    retval

    end

} bind def
/code39 load 0 1 dict put
% --END ENCODER code39--

% --BEGIN ENCODER code93--
% --DESC: Code 93
% --EXAM: THIS IS CODE 93
% --EXOP: includetext includecheck
% --RNDR: renlinear
/code93 {

    0 begin                 % Confine variables to local scope

    /options exch def       % We are given an option string
    /useropts options def
    /barcode exch def       % We are given a barcode string

    /includecheck false def  % Enable/disable checkdigit
    /includetext false def   % Enable/disable text
    /textfont /Courier def
    /textsize 10 def
    /textyoffset -7 def
    /height 1 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /textyoffset textyoffset cvr def
    /height height cvr def
    
    /encs
    [ (131112) (111213) (111312) (111411) (121113)
      (121212) (121311) (111114) (131211) (141111)
      (211113) (211212) (211311) (221112) (221211)
      (231111) (112113) (112212) (112311) (122112)
      (132111) (111123) (111222) (111321) (121122)
      (131121) (212112) (212211) (211122) (211221)
      (221121) (222111) (112122) (112221) (122121)
      (123111) (121131) (311112) (311211) (321111)
      (112131) (113121) (211131) (121221) (312111)
      (311121) (122211) (111141) (1111411)
    ] def

    % Create a string of the available characters
    /barchars (0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%) def

    /barlen barcode length def  % Length of the code    
    barcode {
        (^) search false eq {pop exit} if
        pop pop /barlen barlen 3 sub def
    } loop

    includecheck {
        /sbs barlen 6 mul 25 add string def
    } {
        /sbs barlen 6 mul 13 add string def
    } ifelse
    /txt barlen array def
    
    % Put the start character
    sbs 0 encs 47 get putinterval
    
    /checksum1 0 def /checksum2 0 def

    /i 0 def /j 0 def
    { % loop
        j barlen eq {exit} if
        barcode i 1 getinterval (^) eq {
            % indx is given by the next three characters
            /indx barcode i 1 add 3 getinterval cvi def
            txt j [( ) j 9 mul 9 add textyoffset textfont textsize] put
            /i i 4 add def
        } {
            barchars barcode i 1 getinterval search
            pop                         % Discard true leaving pre
            length /indx exch def       % indx is the length of pre
            pop pop                     % Discard seek and post
            txt j [barchars indx 1 getinterval j 9 mul 9 add textyoffset textfont textsize] put
            /i i 1 add def
        } ifelse
        /enc encs indx get def             % Get the indxth encoding
        sbs j 6 mul 6 add enc putinterval  % Put encoded digit into sbs
        /checksum1 checksum1 barlen j sub 1 sub 20 mod 1 add indx mul add def
        /checksum2 checksum2 barlen j sub 15 mod 1 add indx mul add def
        /j j 1 add def
    } loop
    
    includecheck {
        % Put the first checksum character
        /checksum1 checksum1 47 mod def
        /checksum2 checksum2 checksum1 add 47 mod def
        sbs j 6 mul 6 add encs checksum1 get putinterval
        sbs j 6 mul 12 add encs checksum2 get putinterval
        % Put the end character
        sbs j 6 mul 18 add encs 48 get putinterval
    } {
        % Put the end character
        sbs j 6 mul 6 add encs 48 get putinterval      
    } ifelse

    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) [sbs {48 sub} forall] put
    retval (bhs) [sbs length 1 add 2 idiv {height} repeat] put
    retval (bbs) [sbs length 1 add 2 idiv {0} repeat] put
    includetext {
        retval (txt) txt put
    } if
    retval (opt) useropts put
    retval

    end

} bind def
/code93 load 0 1 dict put
% --END ENCODER code93--

% --BEGIN ENCODER interleaved2of5--
% --DESC: Interleaved 2 of 5 (ITF)
% --EXAM: 24012345678905
% --EXOP: showborder borderwidth=4 borderleft=15 borderright=15 height=0.5 includecheck includetext includecheckintext textyoffset=-10
% --RNDR: renlinear
/interleaved2of5 {

    0 begin         % Confine variables to local scope

    /options exch def               % We are given an option string
    /useropts options def
    /barcode exch def               % We are given a barcode string

    /includecheck false def         % Enable/disable checkdigit
    /includetext false def          % Enable/disable text
    /includecheckintext false def
    /textfont /Courier def
    /textsize 10 def
    /textyoffset -7 def
    /height 1 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /textyoffset textyoffset cvr def
    /height height cvr def
    
    /barlen barcode length def      % Length of the code

    % Prefix 0 to barcode if length is even and including checkdigit
    % or length is odd and not including checkdigit
    barlen 2 mod 0 eq includecheck and          % even & includecheck
    barlen 2 mod 0 ne includecheck not and or { % odd  & !includecheck
        /pad barlen 1 add string def  % Create pad one bigger than barcode
        pad 0 48 put                  % Put ascii 0 at start of pad
        pad 1 barcode putinterval     % Add barcode to the end of pad
        /barcode pad def              % barcode=pad
        /barlen barlen 1 add def      % barlen++
    } if

    % Add checksum to end of barcode
    includecheck {
        /checksum 0 def
        0 1 barlen 1 sub {
            /i exch def
            i 2 mod 0 eq {
                /checksum checksum barcode i get 48 sub 3 mul add def
            } {
                /checksum checksum barcode i get 48 sub add def
            } ifelse
        } for
        /checksum 10 checksum 10 mod sub 10 mod def
        /pad barlen 1 add string def    % Create pad one bigger than barcode
        pad 0 barcode putinterval       % Add barcode to the start of pad
        pad barlen checksum 48 add put  % Add checksum to end of pad
        /barcode pad def                % barcode=pad
        /barlen barlen 1 add def        % barlen++
    } if

    % Create an array containing the character mappings
    /encs
    [ (11331) (31113) (13113) (33111) (11313)
      (31311) (13311) (11133) (31131) (13131)
      (1111)  (3111)
    ] def

    % Create a string of the available characters
    /barchars (0123456789) def
    /sbs barlen 5 mul 8 add string def
    /txt barlen array def

    % Put the start character
    sbs 0 encs 10 get putinterval

    0 2 barlen 1 sub {
    /i exch def
        % Lookup the encodings for two consecutive barcode characters
        barcode i 1 getinterval barchars exch search
        pop                           % Discard true leaving pre
        length /indx exch def         % indx is the length of pre
        pop pop                       % Discard seek and post
        /enca encs indx get def       % Get the indxth encoding

        barcode i 1 add 1 getinterval barchars exch search
        pop                           % Discard true leaving pre
        length /indx exch def         % indx is the length of pre
        pop pop                       % Discard seek and post
        /encb encs indx get def       % Get the indxth encoding

        % Interleave the two character encodings
        /intl enca length 2 mul string def
        0 1 enca length 1 sub {
            /j exch def
            /achar enca j get def
            /bchar encb j get def
            intl j 2 mul achar put
            intl j 2 mul 1 add bchar put
        } for

        sbs i 5 mul 4 add intl putinterval   % Put encoded digit into sbs
        txt i [barcode i 1 getinterval i 9 mul 4 add textyoffset textfont textsize] put
        includecheck includecheckintext not and barlen 2 sub i eq and {
            txt i 1 add [( ) i 1 add 9 mul 4 add textyoffset textfont textsize] put
        } {
            txt i 1 add [barcode i 1 add 1 getinterval i 1 add 9 mul 4 add textyoffset textfont textsize] put
        } ifelse
    } for

    % Put the end character
    sbs barlen 5 mul 4 add encs 11 get putinterval

    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) [sbs {48 sub} forall] put
    retval (bhs) [sbs length 1 add 2 idiv {height} repeat] put
    retval (bbs) [sbs length 1 add 2 idiv {0} repeat] put
    includetext {
        retval (txt) txt put
    } if
    retval (opt) useropts put
    retval

    end

} bind def
/interleaved2of5 load 0 1 dict put
% --END ENCODER interleaved2of5--

% --BEGIN ENCODER rss14--
% --DESC: Reduced Space Symbology 14 (RSS-14)
% --EXAM: 24012345678905
% --EXOP: height=0.3
% --RNDR: renlinear
/rss14 {

    0 begin            % Confine variables to local scope

    /options exch def  % We are given an option string
    /useropts options def
    /barcode exch def  % We are given a barcode string

    /height 1 def
    /linkage false def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
   
    % Create the human readable text
    /txt barcode length array def
    0 1 barcode length 1 sub {
        /i exch def
        txt i [barcode i 1 getinterval 0 0 () 0] put
    } for
 
    /height height cvr def

    /getRSSwidths {
        /oe exch def
        /mw exch def
        /nm exch def
        /val exch def
        /j 0 def /i 0 def {
            /v () def
            mw 1 ne {/v i mw 4 string cvrs def} if
            0 v {48 sub add} forall 4 add nm eq {
                /out [ 4 {1} repeat v {47 sub} forall ] v length 4 getinterval def
                /hasone false def out {1 eq {/hasone true def} if} forall
                oe not hasone or {
                    j val eq {exit} if
                    /j j 1 add def
                } if
            } if
            /i i 1 add def
        } loop
        out
    } bind def

    /binval [barcode {48 sub} forall] def
    /binval [linkage {1} {0} ifelse binval 0 13 getinterval {} forall] def
    
    0 1 12 {
        /i exch def
        binval i 1 add 2 copy get binval i get 4537077 mod 10 mul add put
        binval i binval i get 4537077 idiv put
    } for
    /right binval 13 get 4537077 mod def
    binval 13 2 copy get 4537077 idiv put

    /left 0 def
    /i true def
    0 1 13 {
        /j exch def
        binval j get
        dup 0 eq i and {
            pop
        } {
            /i false def
            /left left 3 -1 roll 10 13 j sub exp cvi mul add def
        } ifelse
    } for
    
    /d1 left 1597 idiv def
    /d2 left 1597 mod def
    /d3 right 1597 idiv def
    /d4 right 1597 mod def

    /tab164 [
        160   0     12 4   8 1  161   1
        960   161   10 6   6 3  80   10
        2014  961   8  8   4 5  31   34
        2714  2015  6  10  3 6  10   70
        2840  2715  4  12  1 8  1    126
    ] def

    /tab154 [
        335   0     5  10  2 7  4   84
        1035  336   7  8   4 5  20  35
        1515  1036  9  6   6 3  48  10
        1596  1516  11 4   8 1  81  1
    ] def

    /i 0 def {
        d1 tab164 i get le {
            tab164 i 1 add 7 getinterval {} forall
            /d1te exch def /d1to exch def
            /d1mwe exch def /d1mwo exch def
            /d1ele exch def /d1elo exch def
            /d1gs exch def
            exit
        } if
        /i i 8 add def
    } loop

    /i 0 def {
        d2 tab154 i get le {
            tab154 i 1 add 7 getinterval {} forall
            /d2te exch def /d2to exch def
            /d2mwe exch def /d2mwo exch def
            /d2ele exch def /d2elo exch def
            /d2gs exch def
            exit
        } if
        /i i 8 add def
    } loop

    /i 0 def {
        d3 tab164 i get le {
            tab164 i 1 add 7 getinterval {} forall
            /d3te exch def /d3to exch def
            /d3mwe exch def /d3mwo exch def
            /d3ele exch def /d3elo exch def
            /d3gs exch def
            exit
        } if
        /i i 8 add def
    } loop

    /i 0 def {
        d4 tab154 i get le {
            tab154 i 1 add 7 getinterval {} forall
            /d4te exch def /d4to exch def
            /d4mwe exch def /d4mwo exch def
            /d4ele exch def /d4elo exch def
            /d4gs exch def
            exit
        } if
        /i i 8 add def
    } loop
    
    /d1wo d1 d1gs sub d1te idiv d1elo d1mwo false getRSSwidths def
    /d1we d1 d1gs sub d1te mod  d1ele d1mwe true  getRSSwidths def
    /d2wo d2 d2gs sub d2to mod  d2elo d2mwo true  getRSSwidths def
    /d2we d2 d2gs sub d2to idiv d2ele d2mwe false getRSSwidths def
    /d3wo d3 d3gs sub d3te idiv d3elo d3mwo false getRSSwidths def
    /d3we d3 d3gs sub d3te mod  d3ele d3mwe true  getRSSwidths def
    /d4wo d4 d4gs sub d4to mod  d4elo d4mwo true  getRSSwidths def
    /d4we d4 d4gs sub d4to idiv d4ele d4mwe false getRSSwidths def

    /d1w 8 array def
    0 1 3 {
        /i exch def
        d1w i 2 mul d1wo i get put
        d1w i 2 mul 1 add d1we i get put
    } for

    /d2w 8 array def
    0 1 3 {
        /i exch def
        d2w 7 i 2 mul sub d2wo i get put
        d2w 6 i 2 mul sub d2we i get put
    } for
    
    /d3w 8 array def
    0 1 3 {
        /i exch def
        d3w 7 i 2 mul sub d3wo i get put
        d3w 6 i 2 mul sub d3we i get put
    } for
    
    /d4w 8 array def
    0 1 3 {
        /i exch def
        d4w i 2 mul d4wo i get put
        d4w i 2 mul 1 add d4we i get put
    } for

    /widths [
        d1w {} forall
        d2w {} forall
        d3w {} forall
        d4w {} forall
    ] def
    
    /checkweights [
        1   3   9   27  2   6   18  54
        58  72  24  8   29  36  12  4
        74  51  17  32  37  65  48  16
        64  34  23  69  49  68  46  59
    ] def

    /checkwidths [
        3 8 2 1 1   3 5 5 1 1   3 3 7 1 1
        3 1 9 1 1   2 7 4 1 1   2 5 6 1 1
        2 3 8 1 1   1 5 7 1 1   1 3 9 1 1
    ] def
    
    /checksum 0 def
    0 1 31 {
        /i exch def
        /checksum checksum widths i get checkweights i get mul add def 
    } for
    /checksum checksum 79 mod def    
    checksum 8 ge {/checksum checksum 1 add def} if
    checksum 72 ge {/checksum checksum 1 add def} if
    /checklt checkwidths checksum 9 idiv 5 mul 5 getinterval def
    /checkrtrev checkwidths checksum 9 mod 5 mul 5 getinterval def
    /checkrt 5 array def
    0 1 4 {
        /i exch def
        checkrt i checkrtrev 4 i sub get put
    } for

    /sbs [
        1 d1w {} forall checklt {} forall d2w {}
        forall d4w {} forall checkrt {} forall d3w {} forall 1 1
    ] def
    
    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) sbs put
    retval (bhs) [sbs length 1 add 2 idiv {height} repeat] put
    retval (bbs) [sbs length 1 add 2 idiv {0} repeat] put   
    retval (txt) txt put
    retval (textxalign) (center) put
    retval (opt) useropts put
    retval

    end

} bind def
/rss14 load 0 1 dict put
% --END ENCODER rss14--

% --BEGIN ENCODER rsslimited--
% --DESC: Reduced Space Symbology Limited (RSS-Limited)
% --EXAM: 00978186074271
% --EXOP: height=0.3
% --RNDR: renlinear
/rsslimited {

    0 begin            % Confine variables to local scope

    /options exch def  % We are given an option string
    /useropts options def
    /barcode exch def  % We are given a barcode string

    /height 1 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
   
    % Create the human readable text
    /txt barcode length array def
    0 1 barcode length 1 sub {
        /i exch def
        txt i [barcode i 1 getinterval 0 0 () 0] put
    } for

    /height height cvr def

    /getRSSwidths {
        /oe exch def
        /el exch def
        /mw exch def
        /nm exch def
        /val exch def
        /j 0 def /i 0 def {
            /v () def
            mw 1 ne {/v i mw el string cvrs def} if
            0 v {48 sub add} forall el add nm eq {
                /out [ el {1} repeat v {47 sub} forall ] v length el getinterval def
                /hasone false def out {1 eq {/hasone true def} if} forall
                oe not hasone or {
                    j val eq {exit} if
                    /j j 1 add def
                } if
            } if
            /i i 1 add def
        } loop
        out
    } bind def
    
    /binval [barcode {48 sub} forall] def
    /binval [binval 0 13 getinterval {} forall] def
    
    0 1 11 {
        /i exch def
        binval i 1 add 2 copy get binval i get 2013571 mod 10 mul add put
        binval i binval i get 2013571 idiv put
    } for
    /d2 binval 12 get 2013571 mod def
    binval 12 2 copy get 2013571 idiv put

    /d1 0 def
    /i true def
    0 1 12 {
        /j exch def
        binval j get
        dup 0 eq i and {
            pop
        } {
            /i false def
            /d1 d1 3 -1 roll 10 12 j sub exp cvi mul add def
        } ifelse
    } for
    
    /tab267 [
        183063   0        17 9   6 3  6538   28
        820063   183064   13 13  5 4  875    728
        1000775  820064   9  17  3 6  28     6454
        1491020  1000776  15 11  5 4  2415   203
        1979844  1491021  11 15  4 5  203    2408
        1996938  1979845  19 7   8 1  17094  1
        2013570  1996939  7  19  1 8  1      16632
    ] def

    /i 0 def {
        d1 tab267 i get le {
            tab267 i 1 add 7 getinterval {} forall
            /d1te exch def /d1to exch def
            /d1mwe exch def /d1mwo exch def
            /d1ele exch def /d1elo exch def
            /d1gs exch def
            exit
        } if
        /i i 8 add def
    } loop

    /i 0 def {
        d2 tab267 i get le {
            tab267 i 1 add 7 getinterval {} forall
            /d2te exch def /d2to exch def
            /d2mwe exch def /d2mwo exch def
            /d2ele exch def /d2elo exch def
            /d2gs exch def
            exit
        } if
        /i i 8 add def
    } loop

    /d1wo d1 d1gs sub d1te idiv d1elo d1mwo 7 false getRSSwidths def    
    /d1we d1 d1gs sub d1te mod  d1ele d1mwe 7 true  getRSSwidths def
    /d2wo d2 d2gs sub d2te idiv d2elo d2mwo 7 false getRSSwidths def    
    /d2we d2 d2gs sub d2te mod  d2ele d2mwe 7 true  getRSSwidths def

    /d1w 14 array def
    0 1 6 {
        /i exch def
        d1w i 2 mul d1wo i get put
        d1w i 2 mul 1 add d1we i get put
    } for

    /d2w 14 array def
    0 1 6 {
        /i exch def
        d2w i 2 mul d2wo i get put
        d2w i 2 mul 1 add d2we i get put
    } for

    /widths [
        d1w {} forall
        d2w {} forall
    ] def
    
    /checkweights [
        1  3  9  27 81 65 17 51 64 14 42 37 22 66
        20 60 2  6  18 54 73 41 34 13 39 28 84 74
    ] def

    /checkseq [
        0 1 43 {} for
        45 52 57
        63 1 66 {} for
        73 1 79 {} for
        82
        126 1 130 {} for
        132
        141 1 146 {} for
        210 1 217 {} for
        220
        316 1 320 {} for
        322 323
        326 337
    ] def
   
    /checksum 0 def
    0 1 27 {
        /i exch def
        /checksum checksum widths i get checkweights i get mul add def
    } for
    /checksum checksum 89 mod def
    /seq checkseq checksum get def
    /swidths seq 21 idiv 8 3 6 false getRSSwidths def
    /bwidths seq 21 mod  8 3 6 false getRSSwidths def

    /checkwidths [0 0 0 0 0 0 0 0 0 0 0 0 1 1] def
    0 1 5 {
        /i exch def
        checkwidths i 2 mul swidths i get put
        checkwidths i 2 mul 1 add bwidths i get put
    } for
    
    /sbs [
        1 d1w {} forall checkwidths {} forall d2w {} forall 1 1
    ] def
    
    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) sbs put
    retval (bhs) [sbs length 1 add 2 idiv {height} repeat] put
    retval (bbs) [sbs length 1 add 2 idiv {0} repeat] put   
    retval (txt) txt put
    retval (textxalign) (center) put
    retval (opt) useropts put
    retval

    end

} bind def
/rsslimited load 0 1 dict put
% --END ENCODER rsslimited--

% --BEGIN ENCODER rssexpanded--
% --DESC: Reduced Space Symbology Expanded (RSS-Expanded)
% --EXAM: 000000010011001010100001000000010000
% --EXOP: height=0.3
% --RNDR: renlinear
/rssexpanded {

    0 begin            % Confine variables to local scope

    /options exch def  % We are given an option string
    /useropts options def
    /barcode exch def  % We are given a barcode string

    /height 1 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /height height cvr def

    /getRSSwidths {
        /oe exch def
        /mw exch def
        /nm exch def
        /val exch def
        /j 0 def /i 0 def {
            /v () def
            mw 1 ne {/v i mw 4 string cvrs def} if
            0 v {48 sub add} forall 4 add nm eq {
                /out [ 4 {1} repeat v {47 sub} forall ] v length 4 getinterval def
                /hasone false def out {1 eq {/hasone true def} if} forall
                /lessfive out 0 get 5 lt def
                oe not hasone lessfive and or {
                    j val eq {exit} if
                    /j j 1 add def
                } if
            } if
            /i i 1 add def
        } loop
        out
    } bind def

    /binval [barcode {48 sub} forall] def
    /datalen binval length 12 idiv def
    
    /tab174 [
        347   0     12 5   7 2  87  4
        1387  348   10 7   5 4  52  20
        2947  1388  8  9   4 5  30  52
        3987  2948  6  11  3 6  10  104
        4191  3988  4  13  1 8  1   204
    ] def

    /dxw datalen array def
    
    0 1 datalen 1 sub {

        /x exch def

        /d binval x 12 mul 12 getinterval def
        /d 0 0 1 11 {/j exch def 2 11 j sub exp cvi d j get mul add} for def

        /j 0 def {
            d tab174 j get le {
                tab174 j 1 add 7 getinterval {} forall
                /dte exch def /dto exch def
                /dmwe exch def /dmwo exch def
                /dele exch def /delo exch def
                /dgs exch def
                exit
            } if
            /j j 8 add def
        } loop

        /dwo d dgs sub dte idiv delo dmwo true  getRSSwidths def
        /dwe d dgs sub dte mod  dele dmwe false getRSSwidths def

        /dw 8 array def        
        x 2 mod 0 eq {                    
            0 1 3 {
                /j exch def
                dw 7 j 2 mul sub dwo j get put
                dw 6 j 2 mul sub dwe j get put
            } for
        } {           
            0 1 3 {
                /j exch def
                dw j 2 mul dwo j get put
                dw j 2 mul 1 add dwe j get put
            } for
        } ifelse

        dxw x dw put

    } for
    
    /widths [
        dxw {{} forall} forall
    ] def

    /checkweights [
        77   96   32   81   27   9    3    1
        20   60   180  118  143  7    21   63
        205  209  140  117  39   13   145  189
        193  157  49   147  19   57   171  91
        132  44   85   169  197  136  186  62
        185  133  188  142  4    12   36   108
        50   87   29   80   97   173  128  113
        150  28   84   41   123  158  52   156
        166  196  206  139  187  203  138  46
        76   17   51   153  37   111  122  155
        146  119  110  107  106  176  129  43
        16   48   144  10   30   90   59   177
        164  125  112  178  200  137  116  109
        70   210  208  202  184  130  179  115
        190  204  68   93   31   151  191  134
        148  22   66   198  172  94   71   2
        40   154  192  64   162  54   18   6
        120  149  25   75   14   42   126  167
        175  199  207  69   23   78   26   79
        103  98   83   38   114  131  182  124
        159  53   88   170  127  183  61   161
        55   165  73   8    24   72   5    15
        89   100  174  58   160  194  135  45
    ] def
    
    /checksum 0 def
    0 1 widths length 1 sub {
        /i exch def
        /checksum checksum widths i get checkweights i get mul add def 
    } for
    /checksum checksum 211 mod datalen 3 sub 211 mul add def

    /i 0 def {
        checksum tab174 i get le {
            tab174 i 1 add 7 getinterval {} forall
            /cte exch def /cto exch def
            /cmwe exch def /cmwo exch def
            /cele exch def /celo exch def
            /cgs exch def
            exit
        } if
        /i i 8 add def
    } loop

    /cwo checksum cgs sub cte idiv celo cmwo true  getRSSwidths def
    /cwe checksum cgs sub cte mod  cele cmwe false getRSSwidths def
    
    /cw 8 array def        
    0 1 3 {
        /i exch def
        cw i 2 mul cwo i get put
        cw i 2 mul 1 add cwe i get put
    } for
    
    /finderwidths [
        1 8 4 1 1    1 1 4 8 1
        3 6 4 1 1    1 1 4 6 3
        3 4 6 1 1    1 1 6 4 3
        3 2 8 1 1    1 1 8 2 3
        2 6 5 1 1    1 1 5 6 2
        2 2 9 1 1    1 1 9 2 2
    ] def

    /finderseq [
        [0 1]
        [0 3 2]
        [0 5 2 7]
        [0 9 2 7 4]
        [0 9 2 7 6 11]
        [0 9 2 7 8 11 10]
        [0 1 2 3 4 5 6 7]
        [0 1 2 3 4 5 6 9 8]
        [0 1 2 3 4 5 6 9 10 11]
        [0 1 2 3 4 7 6 9 8 11 10]
    ] def

    /seq finderseq datalen 2 add 2 idiv 2 sub get def
    /fxw seq length array def
    0 1 seq length 1 sub {
        /x exch def
        fxw x finderwidths seq x get 5 mul 5 getinterval put
    } for
    
    /sbs [
        1
        cw {} forall
        0 1 datalen 1 sub {
            /i exch def
            i 2 mod 0 eq {fxw i 2 idiv get {} forall} if
            dxw i get {} forall
        } for
        1 1
    ] def
    
    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) sbs put
    retval (bhs) [sbs length 1 add 2 idiv {height} repeat] put
    retval (bbs) [sbs length 1 add 2 idiv {0} repeat] put   
    retval (opt) useropts put
    retval

    end

} bind def
/rssexpanded load 0 1 dict put
% --END ENCODER rssexpanded--

% --BEGIN ENCODER pharmacode--
% --DESC: Pharmaceutical Binary Code
% --EXAM: 117480
% --EXOP: showborder
% --RNDR: renlinear
/pharmacode {

    0 begin                 % Confine variables to local scope

    /options exch def       % We are given an option string
    /useropts options def
    /barcode exch def       % We are given a barcode string

    /height 8 2.835 mul 72 div def
    /nwidth 0.5 2.835 mul def
    /wwidth 1.5 2.835 mul def
    /swidth 1.0 2.835 mul def    

    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /height height cvr def
    /nwidth nwidth cvr def
    /wwidth wwidth cvr def
    /swidth swidth cvr def

    % Create the human readable text
    /txt barcode length array def
    0 1 barcode length 1 sub {
        /i exch def
        txt i [barcode i 1 getinterval 0 0 () 0] put
    } for

    % Convert the integer into the paramacode string 
    /barcode barcode cvi 1 add 2 17 string cvrs def
    /barcode barcode 1 barcode length 1 sub getinterval def

    /barlen barcode length def  % Length of the code
    /sbs barlen 2 mul array def

    0 1 barlen 1 sub {
        /i exch def
        /enc barcode i 1 getinterval def
        enc (0) eq {
            sbs i 2 mul nwidth put
        } {
            sbs i 2 mul wwidth put
        } ifelse
        sbs i 2 mul 1 add swidth put
    } for

    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) sbs put
    retval (bhs) [sbs length 1 add 2 idiv {height} repeat] put
    retval (bbs) [sbs length 1 add 2 idiv {0} repeat] put
    retval (txt) txt put
    retval (textxalign) (center) put
    retval (opt) useropts put
    retval

    end

} bind def
/pharmacode load 0 1 dict put
% --END ENCODER pharmacode--

% --BEGIN ENCODER code2of5--
% --DESC: Code 25
% --EXAM: 01234567
% --EXOP: includetext includecheck includecheckintext
% --RNDR: renlinear
/code2of5 {

    % Thanks to Michael Landers

    0 begin                 % Confine variable to local scope

    /options exch def       % We are given an option string
    /useropts options def
    /barcode exch def       % We are given a barcode string

    /includecheck false def
    /includetext false def   % Enable/disable text
    /includecheckintext false def
    /textfont /Courier def
    /textsize 10 def
    /textyoffset -7 def
    /height 1 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /textyoffset textyoffset cvr def
    /height height cvr def
    
    % Create an array containing the character mappings
    /encs
    [ (1111313111) (3111111131) (1131111131) (3131111111)
      (1111311131) (3111311111) (1131311111) (1111113131)
      (3111113111) (1131113111) (313111) (311131)
    ] def

    % Create a string of the available characters
    /barchars (0123456789) def

    /barlen barcode length def            % Length of the code

    includecheck {
        /sbs barlen 10 mul 22 add string def
        /txt barlen 1 add array def
    } {
        /sbs barlen 10 mul 12 add string def
        /txt barlen array def
    } ifelse
    
    % Put the start character
    sbs 0 encs 10 get putinterval

    /checksum 0 def
    
    0 1 barlen 1 sub {
        /i exch def
        % Lookup the encoding for the each barcode character
        barcode i 1 getinterval barchars exch search
        pop                                 % Discard true leaving pre
        length /indx exch def               % indx is the length of pre
        pop pop                             % Discard seek and post
        /enc encs indx get def              % Get the indxth encoding
        sbs i 10 mul 6 add enc putinterval  % Put encoded digit into sbs
        txt i [barcode i 1 getinterval i 14 mul 10 add textyoffset textfont textsize] put
        barlen i sub 2 mod 0 eq {
            /checksum checksum indx add def
        } {            
            /checksum checksum indx 3 mul add def
        } ifelse        
    } for
    
    % Put the checksum and end characters
    includecheck {
        /checksum 10 checksum 10 mod sub 10 mod def
        sbs barlen 10 mul 6 add encs checksum get putinterval
        sbs barlen 10 mul 16 add encs 11 get putinterval
        includecheckintext {
            txt barlen [barchars checksum 1 getinterval barlen 14 mul 10 add textyoffset textfont textsize] put
        } {            
            txt barlen [( ) barlen 14 mul 10 add textyoffset textfont textsize] put
        } ifelse
    } {
        sbs barlen 10 mul 6 add encs 11 get putinterval
    } ifelse
    
    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) [sbs {48 sub} forall] put
    retval (bhs) [sbs length 1 add 2 idiv {height} repeat] put
    retval (bbs) [sbs length 1 add 2 idiv {0} repeat] put
    includetext {
        retval (txt) txt put
    } if
    retval (opt) useropts put
    retval

    end

} bind def
/code2of5 load 0 1 dict put
% --END ENCODER code2of5--

% --BEGIN ENCODER code11--
% --DESC: Code 11
% --EXAM: 0123456789
% --EXOP: includetext includecheck includecheckintext
% --RNDR: renlinear
/code11 {

    0 begin            % Confine variables to local scope

    /options exch def  % We are given an option string
    /useropts options def
    /barcode exch def  % We are given a barcode string

    /includecheck false def
    /includetext false def
    /includecheckintext false def
    /textfont /Courier def
    /textsize 10 def
    /textyoffset -7 def
    /height 1 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /textyoffset textyoffset cvr def
    /height height cvr def
    
    % Create an array containing the character mappings
    /encs
    [ (111131) (311131) (131131) (331111) (113131)
      (313111) (133111) (111331) (311311) (311111)
      (113111) (113311)
    ] def

    % Create a string of the available characters
    /barchars (0123456789-) def

    /barlen barcode length def        % Length of the code

    includecheck {
        barlen 10 ge {
            /sbs barlen 6 mul 24 add string def
            /txt barlen 2 add array def
        } {
            /sbs barlen 6 mul 18 add string def
            /txt barlen 1 add array def
        } ifelse
    } {
        /sbs barlen 6 mul 12 add string def
        /txt barlen array def
    } ifelse

    % Put the start character
    sbs 0 encs 10 get putinterval

    /checksum1 0 def /checksum2 0 def
    
    /xpos 8 def
    0 1 barlen 1 sub {
        /i exch def
        % Lookup the encoding for the each barcode character
        barcode i 1 getinterval barchars exch search
        pop                                % Discard true leaving pre
        length /indx exch def              % indx is the length of pre
        pop pop                            % Discard seek and post
        /enc encs indx get def             % Get the indxth encoding
        sbs i 6 mul 6 add enc putinterval  % Put encoded digit into sbs
        txt i [barcode i 1 getinterval xpos textyoffset textfont textsize] put
        0 1 5 {       % xpos+=width of the character
            /xpos exch enc exch get 48 sub xpos add def
        } for
        /checksum1 checksum1 barlen i sub 1 sub 10 mod 1 add indx mul add def
        /checksum2 checksum2 barlen i sub 9 mod 1 add indx mul add def
    } for
   
    % Put the checksum and end characters
    includecheck {
        /checksum1 checksum1 11 mod def        
        barlen 10 ge {
            /checksum2 checksum2 checksum1 add 11 mod def
            sbs barlen 6 mul 6 add encs checksum1 get putinterval        
            sbs barlen 6 mul 12 add encs checksum2 get putinterval
            includecheckintext {
                txt barlen [barchars checksum1 1 getinterval xpos textyoffset textfont textsize] put
                /enc encs checksum1 get def   
                0 1 5 {       % xpos+=width of the character
                    /xpos exch enc exch get 48 sub xpos add def
                } for
                txt barlen 1 add [barchars checksum2 1 getinterval xpos textyoffset textfont textsize] put
            } {
                txt barlen [() xpos textyoffset textfont textsize] put
                txt barlen 1 add [() xpos textyoffset textfont textsize] put
            } ifelse
            sbs barlen 6 mul 18 add encs 11 get putinterval
        } {
            sbs barlen 6 mul 6 add encs checksum1 get putinterval          
            includecheckintext {
                txt barlen [barchars checksum1 1 getinterval xpos textyoffset textfont textsize] put
            } {
                txt barlen [() xpos textyoffset textfont textsize] put
            } ifelse
            sbs barlen 6 mul 12 add encs 11 get putinterval
        } ifelse
    } {
        sbs barlen 6 mul 6 add encs 11 get putinterval
    } ifelse

    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) [sbs {48 sub} forall] put
    retval (bhs) [sbs length 1 add 2 idiv {height} repeat] put
    retval (bbs) [sbs length 1 add 2 idiv {0} repeat] put
    includetext {
        retval (txt) txt put
    } if
    retval (opt) useropts put
    retval

    end

} bind def
/code11 load 0 1 dict put
% --END ENCODER code11--

% --BEGIN ENCODER rationalizedCodabar--
% --DESC: Rationalized Codabar
% --EXAM: A0123456789B
% --EXOP: includetext includecheck includecheckintext
% --RNDR: renlinear
/rationalizedCodabar {

    0 begin                    % Confine variables to local scope

    /options exch def          % We are given an option string
    /useropts options def
    /barcode exch def          % We are given a barcode string

    /includecheck false def     % Enable/disable checkdigit
    /includetext false def      % Enable/disable text
    /includecheckintext false def
    /textfont /Courier def
    /textsize 10 def
    /textyoffset -7 def
    /height 1 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /textyoffset textyoffset cvr def
    /height height cvr def
    
    % Create an array containing the character mappings
    /encs
    [ (11111331) (11113311) (11131131) (33111111) (11311311)
      (31111311) (13111131) (13113111) (13311111) (31131111)
      (11133111) (11331111) (31113131) (31311131) (31313111)
      (11313131) (11331311) (13131131) (11131331) (11133311)
    ] def

    % Create a string of the available characters
    /barchars (0123456789-$:/.+ABCD) def

    /barlen barcode length def    % Length of the code

    includecheck {
        /sbs barlen 8 mul 8 add string def
        /txt barlen 1 add array def
    } {
        /sbs barlen 8 mul string def
        /txt barlen array def
    } ifelse

    /checksum 0 def
    /xpos 0 def
    0 1 barlen 2 sub {
        /i exch def
        % Lookup the encoding for the each barcode character
        barcode i 1 getinterval barchars exch search
        pop                          % Discard true leaving pre
        length /indx exch def        % indx is the length of pre
        pop pop                      % Discard seek and post
        /enc encs indx get def       % Get the indxth encoding
        sbs i 8 mul enc putinterval  % Put encoded digit into sbs
        txt i [barcode i 1 getinterval xpos textyoffset textfont textsize] put
        0 1 7 {       % xpos+=width of the character
            /xpos exch enc exch get 48 sub xpos add def
        } for
        /checksum checksum indx add def
    } for

    % Find index of last character
    barcode barlen 1 sub 1 getinterval barchars exch search
    pop                          % Discard true leaving pre
    length /indx exch def        % indx is the length of pre
    pop pop                      % Discard seek and post

    includecheck {
        % Put the checksum character
        /checksum checksum indx add def
        /checksum 16 checksum 16 mod sub 16 mod def
        sbs barlen 8 mul 8 sub encs checksum get putinterval
        includecheckintext {
            txt barlen 1 sub [barchars checksum 1 getinterval xpos textyoffset textfont textsize] put
        } {
            txt barlen 1 sub [( ) xpos textyoffset textfont textsize] put
        } ifelse
        0 1 7 {       % xpos+=width of the character
            /xpos exch encs checksum get exch get 48 sub xpos add def
        } for
        % Put the end character
        /enc encs indx get def            % Get the indxth encoding
        sbs barlen 8 mul enc putinterval  % Put encoded digit into sbs
        txt barlen [barcode barlen 1 sub 1 getinterval xpos textyoffset textfont textsize] put
    } {
        % Put the end character
        /enc encs indx get def                  % Get the indxth encoding
        sbs barlen 8 mul 8 sub enc putinterval  % Put encoded digit into sbs
        txt barlen 1 sub [barcode barlen 1 sub 1 getinterval xpos textyoffset textfont textsize] put
    } ifelse

    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) [sbs {48 sub} forall] put
    retval (bhs) [sbs length 1 add 2 idiv {height} repeat] put
    retval (bbs) [sbs length 1 add 2 idiv {0} repeat] put
    includetext {
        retval (txt) txt put
    } if
    retval (opt) useropts put
    retval

    end

} bind def
/rationalizedCodabar load 0 1 dict put
% --END ENCODER rationalizedCodabar--

% --BEGIN ENCODER onecode--
% --DESC: United States Postal Service OneCode
% --EXAM: 0123456709498765432101234567891
% --EXOP: barcolor=FF0000
% --RNDR: renlinear
/onecode {

    0 begin

    /options exch def              % We are given an option string
    /useropts options def
    /barcode exch def              % We are given a barcode string

    /height 0.175 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /height height cvr def

    /barlen barcode length def
 
    % Create the human readable text
    /txt barcode length array def
    0 1 barcode length 1 sub {
        /i exch def
        txt i [barcode i 1 getinterval 0 0 () 0] put
    } for

    /normalize {
        /base exch def
        /num exch def
        num length 1 sub -1 1 {
            /i exch def        
            num i 1 sub 2 copy get num i get base idiv add put
            num i num i get base mod put
        } for
        { %loop - extend input as necessary
            num 0 get base lt {exit} if
            /num [0 num {} forall] def        
            num 0 num 0 get num 1 get base idiv add put
            num 1 num 1 get base mod put
        } loop
        % Trim leading zeros
        /num [/i true def num {dup 0 eq i and {pop} {/i false def} ifelse} forall] def   
        num length 0 eq {/num [0] def} if
        num
    } bind def

    /bigadd {
        2 copy length exch length
        2 copy sub abs /offset exch def
        lt {exch} if
        /a exch def /b exch def    
        0 1 b length 1 sub {
            dup a exch offset add 2 copy get b 5 -1 roll get add put
        } for
        a
    } bind def

    % Conversion of data fields into binary data
    barlen 20 eq {[0]} if
    barlen 25 eq {[1]} if
    barlen 29 eq {[1 0 0 0 0 1]} if
    barlen 31 eq {[1 0 0 0 1 0 0 0 0 1]} if
    /binval exch [barcode 20 barlen 20 sub getinterval {48 sub} forall] bigadd def
    /binval [binval {} forall barcode 0 get 48 sub] def
    /binval [binval {5 mul} forall] [barcode 1 get 48 sub] bigadd 10 normalize def
    /binval [binval {} forall barcode 2 18 getinterval {48 sub} forall] def

    % Conversion of binary data into byte array
    /bytes 13 array def
    /bintmp [binval {} forall] def
    12 -1 0 {
        /i exch def
        0 1 bintmp length 2 sub {
            /j exch def
            bintmp j 1 add 2 copy get bintmp j get 256 mod 10 mul add put
            bintmp j bintmp j get 256 idiv put
        } for
        bytes i bintmp bintmp length 1 sub get 256 mod put
        bintmp bintmp length 1 sub 2 copy get 256 idiv put    
    } for

    % Generation of 11-bit CRC on byte array
    /fcs 2047 def
    /dat bytes 0 get 5 bitshift def
    6 {
        fcs dat xor 1024 and 0 ne {
            /fcs fcs 1 bitshift 3893 xor def 
        } {
            /fcs fcs 1 bitshift def
        } ifelse
        /fcs fcs 2047 and def
        /dat dat 1 bitshift def
    } repeat
    1 1 12 {
        bytes exch get 3 bitshift /dat exch def    
        8 {        
            fcs dat xor 1024 and 0 ne {
                /fcs fcs 1 bitshift 3893 xor def 
            } {
                /fcs fcs 1 bitshift def
            } ifelse
            /fcs fcs 2047 and def
            /dat dat 1 bitshift def
        } repeat
    } for

    % Conversion from binary data to codewords
    /codewords 10 array def
    9 -1 0 {
        /i exch def
        i 9 eq {
            /b 636 def
        } {
            /b 1365 def
        } ifelse
        0 1 binval length 2 sub {
            /j exch def
            binval j 1 add 2 copy get binval j get b mod 10 mul add put
            binval j binval j get b idiv put
        } for   
        codewords i binval binval length 1 sub get b mod put
        binval binval length 1 sub 2 copy get b idiv put
    } for

    % Inserting additional information into codewords
    codewords 9 codewords 9 get 2 mul put
    fcs 1024 and 0 ne {
        codewords 0 codewords 0 get 659 add put
    } if

    % Conversion from codewords to characters
    /tab513 [
        31 7936   47 7808   55 7552   59 7040   61 6016   62 3968   79 7744   87 
      7488   91 6976   93 5952   94 3904  103 7360  107 6848  109 5824  110 3776 
       115 6592  117 5568  118 3520  121 5056  122 3008  124 1984  143 7712  151 
      7456  155 6944  157 5920  158 3872  167 7328  171 6816  173 5792  174 3744 
       179 6560  181 5536  182 3488  185 5024  186 2976  188 1952  199 7264  203 
      6752  205 5728  206 3680  211 6496  213 5472  214 3424  217 4960  218 2912 
       220 1888  227 6368  229 5344  230 3296  233 4832  234 2784  236 1760  241 
      4576  242 2528  244 1504  248  992  271 7696  279 7440  283 6928  285 5904 
       286 3856  295 7312  299 6800  301 5776  302 3728  307 6544  309 5520  310 
      3472  313 5008  314 2960  316 1936  327 7248  331 6736  333 5712  334 3664 
       339 6480  341 5456  342 3408  345 4944  346 2896  348 1872  355 6352  357 
      5328  358 3280  361 4816  362 2768  364 1744  369 4560  370 2512  372 1488 
       376  976  391 7216  395 6704  397 5680  398 3632  403 6448  405 5424  406 
      3376  409 4912  410 2864  412 1840  419 6320  421 5296  422 3248  425 4784 
       426 2736  428 1712  433 4528  434 2480  436 1456  440  944  451 6256  453 
      5232  454 3184  457 4720  458 2672  460 1648  465 4464  466 2416  468 1392 
       472  880  481 4336  482 2288  484 1264  488  752  527 7688  535 7432  539 
      6920  541 5896  542 3848  551 7304  555 6792  557 5768  558 3720  563 6536 
       565 5512  566 3464  569 5000  570 2952  572 1928  583 7240  587 6728  589 
      5704  590 3656  595 6472  597 5448  598 3400  601 4936  602 2888  604 1864 
       611 6344  613 5320  614 3272  617 4808  618 2760  620 1736  625 4552  626 
      2504  628 1480  632  968  647 7208  651 6696  653 5672  654 3624  659 6440 
       661 5416  662 3368  665 4904  666 2856  668 1832  675 6312  677 5288  678 
      3240  681 4776  682 2728  684 1704  689 4520  690 2472  692 1448  696  936 
       707 6248  709 5224  710 3176  713 4712  714 2664  716 1640  721 4456  722 
      2408  724 1384  728  872  737 4328  738 2280  740 1256  775 7192  779 6680 
       781 5656  782 3608  787 6424  789 5400  790 3352  793 4888  794 2840  796 
      1816  803 6296  805 5272  806 3224  809 4760  810 2712  812 1688  817 4504 
       818 2456  820 1432  824  920  835 6232  837 5208  838 3160  841 4696  842 
      2648  844 1624  849 4440  850 2392  852 1368  865 4312  866 2264  868 1240 
       899 6200  901 5176  902 3128  905 4664  906 2616  908 1592  913 4408  914 
      2360  916 1336  929 4280  930 2232  932 1208  961 4216  962 2168  964 1144 
      1039 7684 1047 7428 1051 6916 1053 5892 1054 3844 1063 7300 1067 6788 1069 
      5764 1070 3716 1075 6532 1077 5508 1078 3460 1081 4996 1082 2948 1084 1924 
      1095 7236 1099 6724 1101 5700 1102 3652 1107 6468 1109 5444 1110 3396 1113 
      4932 1114 2884 1116 1860 1123 6340 1125 5316 1126 3268 1129 4804 1130 2756 
      1132 1732 1137 4548 1138 2500 1140 1476 1159 7204 1163 6692 1165 5668 1166 
      3620 1171 6436 1173 5412 1174 3364 1177 4900 1178 2852 1180 1828 1187 6308 
      1189 5284 1190 3236 1193 4772 1194 2724 1196 1700 1201 4516 1202 2468 1204 
      1444 1219 6244 1221 5220 1222 3172 1225 4708 1226 2660 1228 1636 1233 4452 
      1234 2404 1236 1380 1249 4324 1250 2276 1287 7188 1291 6676 1293 5652 1294 
      3604 1299 6420 1301 5396 1302 3348 1305 4884 1306 2836 1308 1812 1315 6292 
      1317 5268 1318 3220 1321 4756 1322 2708 1324 1684 1329 4500 1330 2452 1332 
      1428 1347 6228 1349 5204 1350 3156 1353 4692 1354 2644 1356 1620 1361 4436 
      1362 2388 1377 4308 1378 2260 1411 6196 1413 5172 1414 3124 1417 4660 1418 
      2612 1420 1588 1425 4404 1426 2356 1441 4276 1442 2228 1473 4212 1474 2164 
      1543 7180 1547 6668 1549 5644 1550 3596 1555 6412 1557 5388 1558 3340 1561 
      4876 1562 2828 1564 1804 1571 6284 1573 5260 1574 3212 1577 4748 1578 2700 
      1580 1676 1585 4492 1586 2444 1603 6220 1605 5196 1606 3148 1609 4684 1610 
      2636 1617 4428 1618 2380 1633 4300 1634 2252 1667 6188 1669 5164 1670 3116 
      1673 4652 1674 2604 1681 4396 1682 2348 1697 4268 1698 2220 1729 4204 1730 
      2156 1795 6172 1797 5148 1798 3100 1801 4636 1802 2588 1809 4380 1810 2332 
      1825 4252 1826 2204 1857 4188 1858 2140 1921 4156 1922 2108 2063 7682 2071 
      7426 2075 6914 2077 5890 2078 3842 2087 7298 2091 6786 2093 5762 2094 3714 
      2099 6530 2101 5506 2102 3458 2105 4994 2106 2946 2119 7234 2123 6722 2125 
      5698 2126 3650 2131 6466 2133 5442 2134 3394 2137 4930 2138 2882 2147 6338 
      2149 5314 2150 3266 2153 4802 2154 2754 2161 4546 2162 2498 2183 7202 2187 
      6690 2189 5666 2190 3618 2195 6434 2197 5410 2198 3362 2201 4898 2202 2850 
      2211 6306 2213 5282 2214 3234 2217 4770 2218 2722 2225 4514 2226 2466 2243 
      6242 2245 5218 2246 3170 2249 4706 2250 2658 2257 4450 2258 2402 2273 4322 
      2311 7186 2315 6674 2317 5650 2318 3602 2323 6418 2325 5394 2326 3346 2329 
      4882 2330 2834 2339 6290 2341 5266 2342 3218 2345 4754 2346 2706 2353 4498 
      2354 2450 2371 6226 2373 5202 2374 3154 2377 4690 2378 2642 2385 4434 2401 
      4306 2435 6194 2437 5170 2438 3122 2441 4658 2442 2610 2449 4402 2465 4274 
      2497 4210 2567 7178 2571 6666 2573 5642 2574 3594 2579 6410 2581 5386 2582 
      3338 2585 4874 2586 2826 2595 6282 2597 5258 2598 3210 2601 4746 2602 2698 
      2609 4490 2627 6218 2629 5194 2630 3146 2633 4682 2641 4426 2657 4298 2691 
      6186 2693 5162 2694 3114 2697 4650 2705 4394 2721 4266 2753 4202 2819 6170 
      2821 5146 2822 3098 2825 4634 2833 4378 2849 4250 2881 4186 2945 4154 3079 
      7174 3083 6662 3085 5638 3086 3590 3091 6406 3093 5382 3094 3334 3097 4870 
      3107 6278 3109 5254 3110 3206 3113 4742 3121 4486 3139 6214 3141 5190 3145 
      4678 3153 4422 3169 4294 3203 6182 3205 5158 3209 4646 3217 4390 3233 4262 
      3265 4198 3331 6166 3333 5142 3337 4630 3345 4374 3361 4246 3393 4182 3457 
      4150 3587 6158 3589 5134 3593 4622 3601 4366 3617 4238 3649 4174 3713 4142 
      3841 4126 4111 7681 4119 7425 4123 6913 4125 5889 4135 7297 4139 6785 4141 
      5761 4147 6529 4149 5505 4153 4993 4167 7233 4171 6721 4173 5697 4179 6465 
      4181 5441 4185 4929 4195 6337 4197 5313 4201 4801 4209 4545 4231 7201 4235 
      6689 4237 5665 4243 6433 4245 5409 4249 4897 4259 6305 4261 5281 4265 4769 
      4273 4513 4291 6241 4293 5217 4297 4705 4305 4449 4359 7185 4363 6673 4365 
      5649 4371 6417 4373 5393 4377 4881 4387 6289 4389 5265 4393 4753 4401 4497 
      4419 6225 4421 5201 4425 4689 4483 6193 4485 5169 4489 4657 4615 7177 4619 
      6665 4621 5641 4627 6409 4629 5385 4633 4873 4643 6281 4645 5257 4649 4745 
      4675 6217 4677 5193 4739 6185 4741 5161 4867 6169 4869 5145 5127 7173 5131 
      6661 5133 5637 5139 6405 5141 5381 5155 6277 5157 5253 5187 6213 5251 6181 
      5379 6165 5635 6157 6151 7171 6155 6659 6163 6403 6179 6275 6211 5189 4681 
      4433 4321 3142 2634 2386 2274 1612 1364 1252  856  744  496 
    ] def

    /tab213 [
         3 6144    5 5120    6 3072    9 4608   10 2560   12 1536   17 4352   18 
      2304   20 1280   24  768   33 4224   34 2176   36 1152   40  640   48  384 
        65 4160   66 2112   68 1088   72  576   80  320   96  192  129 4128  130 
      2080  132 1056  136  544  144  288  257 4112  258 2064  260 1040  264  528 
       513 4104  514 2056  516 1032 1025 4100 1026 2052 2049 4098 4097 2050 1028 
       520  272  160
    ] def

    /chars 10 array def
    0 1 9 {
        /i exch def
        codewords i get dup 1286 le {
            tab513 exch get 
        } {
            tab213 exch 1287 sub get
        } ifelse
        chars i 3 -1 roll put
    } for

    9 -1 0 {
        /i exch def
        2 i exp cvi fcs and 0 ne {
            chars i chars i get 8191 xor put
        } if
    } for

    % Conversion from characters to the OneCode encoding
    /barmap [
        7 2 4 3    1 10 0 0   9 12 2 8   5 5 6 11   8 9 3 1
        0 1 5 12   2 5 1 8    4 4 9 11   6 3 8 10   3 9 7 6
        5 11 1 4   8 5 2 12   9 10 0 2   7 1 6 7    3 6 4 9
        0 3 8 6    6 4 2 7    1 1 9 9    7 10 5 2   4 0 3 8
        6 2 0 4    8 11 1 0   9 8 3 12   2 6 7 7    5 1 4 10
        1 12 6 9   7 3 8 0    5 8 9 7    4 6 2 10   3 4 0 5
        8 4 5 7    7 11 1 9   6 0 9 6    0 6 4 8    2 1 3 2
        5 9 8 12   4 11 6 1   9 5 7 4    3 3 1 2    0 7 2 0
        1 3 4 1    6 10 3 5   8 7 9 4    2 11 5 6   0 8 7 12
        4 2 8 1    5 10 3 0   9 3 0 9    6 5 2 4    7 8 1 7
        5 0 4 5    2 3 0 10   6 12 9 2   3 11 1 6   8 8 7 9
        5 4 0 11   1 5 2 2    9 1 4 12   8 3 6 6    7 0 3 7
        4 7 7 5    0 12 1 11  2 9 9 0    6 8 5 3    3 10 8 2
    ] def

    /bbs 65 array def    
    /bhs 65 array def
    0 1 64 {
        /i exch def
        /dec chars barmap i 4 mul get get 2 barmap i 4 mul 1 add get exp cvi and 0 ne def
        /asc chars barmap i 4 mul 2 add get get 2 barmap i 4 mul 3 add get exp cvi and 0 ne def
        dec not asc not and {
            bbs i 3 height mul 8 div put
            bhs i 2 height mul 8 div put
        } if
        dec not asc and {
            bbs i 3 height mul 8 div put
            bhs i 5 height mul 8 div put        
        } if
        dec asc not and {
            bbs i 0 height mul 8 div put
            bhs i 5 height mul 8 div put        
        } if
        dec asc and {
            bbs i 0 height mul 8 div put
            bhs i 8 height mul 8 div put        
        } if
    } for
    
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (bbs) bbs put
    retval (bhs) bhs put
    retval (sbs) [bhs length 1 sub {1.44 1.872} repeat 1.44] put    
    retval (txt) txt put
    retval (textxalign) (center) put
    retval (opt) useropts put
    retval

    end

} bind def
/onecode load 0 1 dict put
% --END ENCODER onecode--

% --BEGIN ENCODER postnet--
% --DESC: United States Postal Service Postnet
% --EXAM: 012345
% --EXOP: includetext includecheckintext
% --RNDR: renlinear
/postnet {

    0 begin

    /options exch def              % We are given an option string
    /useropts options def
    /barcode exch def              % We are given a barcode string

    /includetext false def          % Enable/disable text
    /includecheckintext false def
    /textfont /Courier def
    /textsize 10 def
    /textyoffset -7 def
    /height 0.125 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /textyoffset textyoffset cvr def
    /height height cvr def
    
    /barlen barcode length def

    % Create an array containing the character mappings
    /encs
    [ (55222) (22255) (22525) (22552) (25225)
      (25252) (25522) (52225) (52252) (52522)
      (5) (5)
    ] def

    % Create a string of the available characters
    /barchars (0123456789) def

    /bhs barlen 5 mul 7 add array def
    /txt barlen 1 add array def

    % Put start character
    /enc encs 10 get def
    /heights enc length array def
    0 1 enc length 1 sub {
        /j exch def
        heights j enc j 1 getinterval cvi height mul 5 div put
    } for
    bhs 0 heights putinterval   % Put encoded digit into sbs

    /checksum 0 def
    0 1 barlen 1 sub {
        /i exch def
        % Lookup the encoding for the each barcode character
        barcode i 1 getinterval barchars exch search
        pop                                 % Discard true leaving pre
        length /indx exch def               % indx is the length of pre
        pop pop                             % Discard seek and post
        /enc encs indx get def              % Get the indxth encoding
        /heights enc length array def
        0 1 enc length 1 sub {
            /j exch def
            heights j enc j 1 getinterval cvi height mul 5 div put
        } for
        bhs i 5 mul 1 add heights putinterval   % Put encoded digit into sbs
        txt i [barcode i 1 getinterval i 5 mul 1 add 3.312 mul textyoffset textfont textsize] put
        /checksum checksum indx add def     % checksum+=indx
    } for

    % Put the checksum character
    /checksum 10 checksum 10 mod sub 10 mod def
    /enc encs checksum get def
    /heights enc length array def
    0 1 enc length 1 sub {
        /j exch def
        heights j enc j 1 getinterval cvi height mul 5 div put
    } for
    bhs barlen 5 mul 1 add heights putinterval  
    
    includecheckintext {
        txt barlen [barchars checksum 1 getinterval barlen 5 mul 1 add 3.312 mul textyoffset textfont textsize] put
    } {
        txt barlen [( ) barlen 5 mul 1 add 72 mul 25 div textyoffset textfont textsize] put
    } ifelse
    
    % Put end character
    /enc encs 11 get def
    /heights enc length array def
    0 1 enc length 1 sub {
        /j exch def
        heights j enc j 1 getinterval cvi height mul 5 div put
    } for
    bhs barlen 5 mul 6 add heights putinterval  

    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (bhs) bhs put
    retval (bbs) [bhs length {0} repeat] put
    retval (sbs) [bhs length 1 sub {1.44 1.872} repeat 1.44] put
    includetext {
        retval (txt) txt put
    } if
    retval (opt) useropts put
    retval

    end

} bind def
/postnet load 0 1 dict put
% --END ENCODER postnet--

% --BEGIN ENCODER royalmail--
% --DESC: Royal Mail 4 State Customer Code (RM4SCC)
% --EXAM: LE28HS9Z
% --EXOP: includetext includecheckintext barcolor=FF0000
% --RNDR: renlinear
/royalmail {

    0 begin

    /options exch def              % We are given an option string
    /useropts options def
    /barcode exch def              % We are given a barcode string

    /includetext false def          % Enable/disable text
    /includecheckintext false def
    /textfont /Courier def
    /textsize 10 def
    /textyoffset -7 def
    /height 0.175 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /textyoffset textyoffset cvr def
    /height height cvr def
    
    % Create an array containing the character mappings
    /encs
    [ (3300) (2211) (2301) (2310) (3201) (3210) 
      (1122) (0033) (0123) (0132) (1023) (1032) 
      (1302) (0213) (0303) (0312) (1203) (1212) 
      (1320) (0231) (0321) (0330) (1221) (1230) 
      (3102) (2013) (2103) (2112) (3003) (3012) 
      (3120) (2031) (2121) (2130) (3021) (3030) 
      (2) (3)
    ] def

    % Create a string of the available characters
    /barchars (ZUVWXY501234B6789AHCDEFGNIJKLMTOPQRS) def

    /barlen barcode length def
    /encstr barlen 4 mul 6 add string def
    /txt barlen 1 add array def

    % Put start character
    encstr 0 encs 36 get putinterval
    
    /checksumrow 0 def
    /checksumcol 0 def
    0 1 barlen 1 sub {
        /i exch def
        % Lookup the encoding for the each barcode character
        barcode i 1 getinterval barchars exch search
        pop                                 % Discard true leaving pre
        length /indx exch def               % indx is the length of pre
        pop pop                             % Discard seek and post
        /enc encs indx get def              % Get the indxth encoding
        encstr i 4 mul 1 add enc putinterval
        txt i [barcode i 1 getinterval i 4 mul 1 add 3.312 mul textyoffset textfont textsize] put
        /checksumrow checksumrow indx 6 idiv add def
        /checksumcol checksumcol indx 6 mod add def 
    } for

    % Put the checksum character
    /checksum checksumrow 6 mod 6 mul checksumcol 6 mod add def
    /enc encs checksum get def
    encstr barlen 4 mul 1 add enc putinterval
    includecheckintext {
        txt barlen [barchars checksum 1 getinterval barlen 4 mul 1 add 3.312 mul textyoffset textfont textsize] put
    } {
        txt barlen [( ) barlen 4 mul 1 add 3.312 mul textyoffset textfont textsize] put
    } ifelse
    
    % Put end character
    encstr barlen 4 mul 5 add encs 37 get putinterval  

    /bbs encstr length array def    
    /bhs encstr length array def
    0 1 encstr length 1 sub {
        /i exch def
        /enc encstr i 1 getinterval def
        enc (0) eq {
            bbs i 3 height mul 8 div put
            bhs i 2 height mul 8 div put
        } if
        enc (1) eq {
            bbs i 0 height mul 8 div put
            bhs i 5 height mul 8 div put
        } if
        enc (2) eq {
            bbs i 3 height mul 8 div put
            bhs i 5 height mul 8 div put
        } if
        enc (3) eq {
            bbs i 0 height mul 8 div put
            bhs i 8 height mul 8 div put
        } if
    } for
    
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (bbs) bbs put
    retval (bhs) bhs put
    retval (sbs) [bhs length 1 sub {1.44 1.872} repeat 1.44] put
    includetext {
        retval (txt) txt put
    } if
    retval (opt) useropts put
    retval

    end

} bind def
/royalmail load 0 1 dict put
% --END ENCODER royalmail--

% --BEGIN ENCODER auspost--
% --DESC: AusPost 4 State Customer Code
% --EXAM: 5956439111ABA 9
% --EXOP: includetext custinfoenc=character
% --RNDR: renlinear
/auspost {

    0 begin

    /options exch def              % We are given an option string
    /useropts options def
    /barcode exch def              % We are given a barcode string

    /includetext false def         % Enable/disable text
    /textfont /Courier def
    /textsize 10 def
    /textyoffset -7 def
    /height 0.175 def
    /custinfoenc (character) def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /textyoffset textyoffset cvr def
    /height height cvr def

    % Create an array containing the character mappings
    /encs
    [ (000) (001) (002) (010) (011) (012) (020) (021)
      (022) (100) (101) (102) (110) (111) (112) (120)
      (121) (122) (200) (201) (202) (210) (211) (212)
      (220) (221) (222) (300) (301) (302) (310) (311)
      (312) (320) (321) (322) (023) (030) (031) (032)
      (033) (103) (113) (123) (130) (131) (132) (133)
      (203) (213) (223) (230) (231) (232) (233) (303)
      (313) (323) (330) (331) (332) (333) (003) (013)
      (00) (01) (02) (10) (11) (12) (20) (21) (22) (30)
      (13) (3)
    ] def

    % Create a string of the available characters
    /barchars (ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz #) def
    
    /barlen barcode length def
    barcode 0 2 getinterval (11) eq {37} if
    barcode 0 2 getinterval (45) eq {37} if
    barcode 0 2 getinterval (59) eq {52} if
    barcode 0 2 getinterval (62) eq {67} if
    /encstr exch string def
    /txt barlen 2 sub array def

    % Put start character
    encstr 0 encs 74 get putinterval

    % Encode the FCC
    0 1 1 {
        /i exch def       
        encs barcode i 1 getinterval cvi 64 add get
        encstr i 2 mul 2 add 3 2 roll putinterval
    } for
    
    % Encode the DPID
    2 1 9 {
        /i exch def       
        encs barcode i 1 getinterval cvi 64 add get
        encstr i 2 mul 2 add 3 2 roll putinterval
        txt i 2 sub [barcode i 1 getinterval i 2 sub 2 mul 6 add 3.312 mul textyoffset textfont textsize] put
    } for
    
    % Encode the customer information   
    custinfoenc (numeric) eq {
        0 1 barlen 11 sub {
            /i exch def
            encs barcode i 10 add 1 getinterval cvi 64 add get
            encstr i 2 mul 22 add 3 2 roll putinterval
            txt i 8 add [barcode i 10 add 1 getinterval i 2 mul 22 add 3.312 mul textyoffset textfont textsize] put
        } for        
        /ciflen barlen 10 sub 2 mul def
    } {
        0 1 barlen 11 sub {
            /i exch def           
            barcode i 10 add 1 getinterval barchars exch search
            pop                                
            length /indx exch def           
            pop pop                            
            /enc encs indx get def          
            encstr i 3 mul 22 add enc putinterval
            txt i 8 add [barcode i 10 add 1 getinterval i 3 mul 22 add 3.312 mul textyoffset textfont textsize] put
        } for        
        /ciflen barlen 10 sub 3 mul def
    } ifelse

    % Add any filler characters
    22 ciflen add 1 encstr length 14 sub {        
        encstr exch encs 75 get putinterval
    } for
    
    % Create the 64x64 Reed-Solomon table
    /rstable 64 64 mul array def
    rstable 0 [ 64 {0} repeat ] putinterval
    rstable 64 [ 0 1 63 {} for ] putinterval
    /prev 1 def
    64 {       
        /next prev 1 bitshift def
        next 64 and 0 ne {
            /next next 67 xor def
        } if        
        0 1 63 {
            /j exch def
            /nextcell {rstable 64 next mul j add} def
            nextcell rstable 64 prev mul j add get 1 bitshift put
            nextcell get 64 and 0 ne {
                nextcell nextcell get 67 xor put
            } if
        } for
        /prev next def
    } repeat
    
    % Calculate the Reed-Solomon codes for triples
    /rscodes encstr length 16 sub 3 idiv 4 add array def
    rscodes 0 [ 4 {0} repeat ] putinterval
    2 3 encstr length 16 sub {
        /i exch def
        rscodes rscodes length i 2 sub 3 idiv sub 1 sub
        encstr i 1 getinterval cvi 16 mul
        encstr i 1 add 1 getinterval cvi 4 mul add
        encstr i 2 add 1 getinterval cvi add        
        put
    } for    
    rscodes length 5 sub -1 0 {
       /i exch def
       0 1 4 {
           /j exch def
           rscodes i j add rscodes i j add get
           rstable 64 [48 17 29 30 1] j get mul rscodes i 4 add get add get
           xor put
       } for
    } for
    /checkcode (000000000000) 12 string copy def
    0 1 3 {
        /i exch def
        /enc rscodes 3 i sub get 4 3 string cvrs def
        checkcode i 3 mul 3 enc length sub add enc putinterval
    } for
    
    % Put checkcode and end characters
    encstr encstr length 14 sub checkcode putinterval
    encstr encstr length 2 sub encs 74 get putinterval 

    /bbs encstr length array def    
    /bhs encstr length array def
    0 1 encstr length 1 sub {
        /i exch def
        /enc encstr i 1 getinterval def
        enc (0) eq {
            bbs i 0 height mul 8 div put
            bhs i 8 height mul 8 div put
        } if
        enc (1) eq {
            bbs i 3 height mul 8 div put
            bhs i 5 height mul 8 div put
        } if
        enc (2) eq {
            bbs i 0 height mul 8 div put
            bhs i 5 height mul 8 div put
        } if
        enc (3) eq {
            bbs i 3 height mul 8 div put
            bhs i 2 height mul 8 div put
        } if
    } for   
    
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (bbs) bbs put
    retval (bhs) bhs put
    retval (sbs) [bhs length 1 sub {1.44 1.872} repeat 1.44] put
    includetext {
        retval (txt) txt put
    } if
    retval (opt) useropts put
    retval

    end

} bind def
/auspost load 0 1 dict put
% --END ENCODER auspost--

% --BEGIN ENCODER kix--
% --DESC: Royal Dutch TPG Post KIX 4-State Barcode
% --EXAM: 1231FZ13XHS
% --EXOP: includetext includecheckintext
% --RNDR: renlinear
/kix {

    0 begin

    /options exch def              % We are given an option string
    /useropts options def
    /barcode exch def              % We are given a barcode string

    /includetext false def          % Enable/disable text
    /includecheckintext false def
    /textfont /Courier def
    /textsize 10 def
    /textyoffset -7 def
    /height 0.175 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /textyoffset textyoffset cvr def
    /height height cvr def
    
    % Create an array containing the character mappings
    /encs
    [ (0033) (0123) (0132) (1023) (1032) (1122)
      (0213) (0303) (0312) (1203) (1212) (1302) 
      (0231) (0321) (0330) (1221) (1230) (1320)
      (2013) (2103) (2112) (3003) (3012) (3102)
      (2031) (2121) (2130) (3021) (3030) (3120) 
      (2211) (2301) (2310) (3201) (3210) (3300) 
    ] def

    % Create a string of the available characters
    /barchars (0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ) def

    /barlen barcode length def
    /encstr barlen 4 mul string def
    /txt barlen array def
    
    0 1 barlen 1 sub {
        /i exch def
        % Lookup the encoding for the each barcode character
        barcode i 1 getinterval barchars exch search
        pop                                 % Discard true leaving pre
        length /indx exch def               % indx is the length of pre
        pop pop                             % Discard seek and post
        /enc encs indx get def              % Get the indxth encoding
        encstr i 4 mul enc putinterval
        txt i [barcode i 1 getinterval i 4 mul 3.312 mul textyoffset textfont textsize] put
    } for

    /bbs encstr length array def    
    /bhs encstr length array def
    0 1 encstr length 1 sub {
        /i exch def
        /enc encstr i 1 getinterval def
        enc (0) eq {
            bbs i 3 height mul 8 div put
            bhs i 2 height mul 8 div put
        } if
        enc (1) eq {
            bbs i 0 height mul 8 div put
            bhs i 5 height mul 8 div put
        } if
        enc (2) eq {
            bbs i 3 height mul 8 div put
            bhs i 5 height mul 8 div put
        } if
        enc (3) eq {
            bbs i 0 height mul 8 div put
            bhs i 8 height mul 8 div put
        } if
    } for
    
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (bbs) bbs put
    retval (bhs) bhs put
    retval (sbs) [bhs length 1 sub {1.44 1.872} repeat 1.44] put
    includetext {
        retval (txt) txt put
    } if
    retval (opt) useropts put
    retval

    end

} bind def
/kix load 0 1 dict put
% --END ENCODER kix--

% --BEGIN ENCODER msi--
% --DESC: MSI Modified Plessey
% --EXAM: 0123456789
% --EXOP: includetext includecheck includecheckintext
% --RNDR: renlinear
/msi {

    0 begin                 % Confine variables to local scope

    /options exch def       % We are given an option string
    /useropts options def
    /barcode exch def       % We are given a barcode string

    /includecheck false def  % Enable/disable checkdigit
    /includetext false def   % Enable/disable text
    /includecheckintext false def
    /textfont /Courier def
    /textsize 10 def
    /textyoffset -7 def
    /height 1 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /textyoffset textyoffset cvr def
    /height height cvr def
    
    % Create an array containing the character mappings
    /encs
    [ (13131313) (13131331) (13133113) (13133131) (13311313)
      (13311331) (13313113) (13313131) (31131313) (31131331)
      (31) (131)
    ] def

    % Create a string of the available characters
    /barchars (0123456789) def

    /barlen barcode length def     % Length of the code

    includecheck {
        /sbs barlen 8 mul 13 add string def
        /txt barlen 1 add array def
    } {
        /sbs barlen 8 mul 5 add string def
        /txt barlen array def
    } ifelse


    % Put start character
    sbs 0 encs 10 get putinterval
    /checksum 0 def

    0 1 barlen 1 sub {
        /i exch def
        % Lookup the encoding for the each barcode character
        barcode i 1 getinterval barchars exch search
        pop                                % Discard true leaving pre
        length /indx exch def              % indx is the length of pre
        pop pop                            % Discard seek and post
        /enc encs indx get def             % Get the indxth encoding
        sbs i 8 mul 2 add enc putinterval  % Put encoded digit into sbs
        txt i [barcode i 1 getinterval i 16 mul 4 add textyoffset textfont textsize] put
        barlen i sub 2 mod 0 eq {
            /checksum indx checksum add def
        } {
            /checksum indx 2 mul dup 10 idiv add checksum add def
        } ifelse
    } for

    % Put the checksum and end characters
    includecheck {
        /checksum 10 checksum 10 mod sub 10 mod def
        sbs barlen 8 mul 2 add encs checksum get putinterval
        includecheckintext {
            txt barlen [barchars checksum 1 getinterval barlen 16 mul 4 add textyoffset textfont textsize] put
        } {
            txt barlen [( ) barlen 16 mul 4 add textyoffset textfont textsize] put
        } ifelse
        sbs barlen 8 mul 10 add encs 11 get putinterval
    } {
        sbs barlen 8 mul 2 add encs 11 get putinterval
    } ifelse

    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) [sbs {48 sub} forall] put
    retval (bhs) [sbs length 1 add 2 idiv {height} repeat] put
    retval (bbs) [sbs length 1 add 2 idiv {0} repeat] put
    includetext {
        retval (txt) txt put
    } if
    retval (opt) useropts put
    retval

    end

} bind def
/msi load 0 1 dict put
% --END ENCODER msi--

% --BEGIN ENCODER plessey--
% --DESC: Plessey
% --EXAM: 01234ABCD
% --EXOP: includetext includecheckintext
% --RNDR: renlinear
/plessey {

    0 begin                  % Confine variables to local scope

    /options exch def        % We are given an option string
    /useropts options def
    /barcode exch def        % We are given a barcode string

    /includetext false def    % Enable/disable text
    /includecheckintext false def
    /textfont /Courier def
    /textsize 10 def
    /textyoffset -7 def
    /height 1 def
    
    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /textyoffset textyoffset cvr def
    /height height cvr def
    
    % Create an array containing the character mappings
    /encs
    [ (13131313) (31131313) (13311313) (31311313)
      (13133113) (31133113) (13313113) (31313113)
      (13131331) (31131331) (13311331) (31311331)
      (13133131) (31133131) (13313131) (31313131)
      (31311331) (331311313)
    ] def

    % Create a string of the available characters
    /barchars (0123456789ABCDEF) def

    /barlen barcode length def     % Length of the code
    /sbs barlen 8 mul 33 add string def
    /txt barlen 2 add array def
    /checkbits barlen 4 mul 8 add array def
    checkbits barlen 4 mul [ 0 0 0 0 0 0 0 0 ] putinterval

    % Put start character
    sbs 0 encs 16 get putinterval

    0 1 barlen 1 sub {
        /i exch def
        % Lookup the encoding for the each barcode character
        barcode i 1 getinterval barchars exch search
        pop                                % Discard true leaving pre
        length /indx exch def              % indx is the length of pre
        pop pop                            % Discard seek and post
        /enc encs indx get def             % Get the indxth encoding
        sbs i 8 mul 8 add enc putinterval  % Put encoded digit into sbs
        txt i [barcode i 1 getinterval i 16 mul 16 add textyoffset textfont textsize] put
        checkbits i 4 mul [
                indx 1 and
                indx -1 bitshift 1 and
                indx -2 bitshift 1 and
                indx -3 bitshift
        ] putinterval
    } for

    % Checksum is last 8 bits of a CRC using a salt
    /checksalt [ 1 1 1 1 0 1 0 0 1 ] def
    0 1 barlen 4 mul 1 sub {
        /i exch def
        checkbits i get 1 eq {
            0 1 8 {
                /j exch def
                checkbits i j add checkbits i j add get checksalt j get xor put
            } for
        } if
    } for

    % Calculate the value of the checksum digits
    /checkval 0 def
    0 1 7 {
        /i exch def
        /checkval checkval 2 7 i sub exp cvi checkbits barlen 4 mul i add get mul add def
    } for

    % Put the checksum characters
    /checksum1 checkval -4 bitshift def
    /checksum2 checkval 15 and def
    sbs barlen 8 mul 8 add encs checksum1 get putinterval
    sbs barlen 8 mul 16 add encs checksum2 get putinterval
    includecheckintext {
        txt barlen [barchars checksum1 1 getinterval barlen 16 mul 16 add textyoffset textfont textsize] put
        txt barlen 1 add [barchars checksum2 1 getinterval barlen 1 add 16 mul 16 add textyoffset textfont textsize] put
    } {
        txt barlen [( ) barlen 16 mul 16 add textyoffset textfont textsize] put
        txt barlen 1 add [( ) barlen 1 add 16 mul 16 add textyoffset textfont textsize] put
    } ifelse

    % Put end character
    sbs barlen 8 mul 24 add encs 17 get putinterval

    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) [sbs {48 sub} forall] put
    retval (bhs) [sbs length 1 add 2 idiv {height} repeat] put
    retval (bbs) [sbs length 1 add 2 idiv {0} repeat] put
    includetext {
        retval (txt) txt put
    } if
    retval (opt) useropts put
    retval

    end

} bind def
/plessey load 0 1 dict put
% --END ENCODER plessey--

% --BEGIN ENCODER raw--
% --DESC: Raw bar space succession for custom symbologies 
% --EXAM: 331132131313411122131311333213114131131221323
% --EXOP: height=0.5
% --RNDR: renlinear
/raw {

    0 begin                  % Confine variables to local scope

    /options exch def        % We are given an option string
    /useropts options def
    /sbs exch def        % We are given a barcode string

    /height 1 def

    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    /height height cvr def

    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) [sbs {48 sub} forall] put
    retval (bhs) [sbs length 1 add 2 idiv {height} repeat] put
    retval (bbs) [sbs length 1 add 2 idiv {0} repeat] put 
    retval (opt) useropts put
    retval

    end

} bind def
/raw load 0 1 dict put
% --END ENCODER raw--

% --BEGIN ENCODER symbol--
% --DESC: Miscellaneous symbols
% --EXAM: fima
% --EXOP: backgroundcolor=DD000011
% --RNDR: renlinear
/symbol {

    0 begin            % Confine variables to local scope

    /options exch def  % We are given an option string
    /barcode exch def  % We are given a barcode string

    barcode (fima) eq {
        /sbs [2.25 2.25 2.25 11.25 2.25 11.25 2.25 2.25 2.25] def
        /bhs [.625 .625 .625 .625 .625] def
        /bbs [0 0 0 0 0] def
    } if

    barcode (fimb) eq {
        /sbs [2.25 6.75 2.25 2.25 2.25 6.25 2.25 2.25 2.25 6.75 2.25] def
        /bhs [.625 .625 .625 .625 .625 .625] def
        /bbs [0 0 0 0 0 0] def
    } if

    barcode (fimc) eq {
        /sbs [2.25 2.25 2.25 6.75 2.25 6.75 2.25 6.75 2.25 2.25 2.25] def
        /bhs [.625 .625 .625 .625 .625 .625] def
        /bbs [0 0 0 0 0 0] def
    } if
    
    barcode (fimd) eq {
        /sbs [2.25 2.25 2.25 2.25 2.25 6.75 2.25 6.75 2.25 2.25 2.25 2.25 2.25] def
        /bhs [.625 .625 .625 .625 .625 .625 .625] def
        /bbs [0 0 0 0 0 0 0] def
    } if
    
    % Return the arguments
    /retval 8 dict def
    retval (ren) (renlinear) put
    retval (sbs) sbs put
    retval (bhs) bhs put
    retval (bbs) bbs put
    retval (opt) options put
    retval

    end

} bind def
/symbol load 0 1 dict put
% --END ENCODER symbol--

% --BEGIN ENCODER pdf417--
% --DESC: PDF417
% --EXAM: ^453^178^121^239
% --EXOP: columns=2 rows=10
% --RNDR: renmatrix
/pdf417 {

    0 begin

    /options exch def
    /useropts options def
    /barcode exch def

    /compact false def
    /eclevel -1 def
    /columns 0 def
    /rows 0 def
    /rowmult 3 def

    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop

    /eclevel eclevel cvi def
    /columns columns cvi def
    /rows rows cvi def
    /rowmult rowmult cvr def

    % Split the input barcode into an array of codewords
    /datcws barcode length array def
    /i 0 def /j 0 def
    { % loop
        i barcode length eq {exit} if
        /cw barcode i 1 add 3 getinterval cvi def
        datcws j cw put
        /i i 4 add def
        /j j 1 add def
    } loop
    /datcws datcws 0 j getinterval def

    % Determine the error correction level if unspecified
    /m datcws length def
    eclevel -1 eq {
        m 40 le {/eclevel 2 def} if
        m 41 ge m 160 le and {/eclevel 3 def} if
        m 161 ge m 320 le and {/eclevel 4 def} if
        m 321 ge {/eclevel 5 def} if
    } if

    % Reduce the error level so that it does not cause an excessive number of codewords
    /maxeclevel 928 1 sub m sub ln 2 ln div cvi 1 sub def
    eclevel maxeclevel gt {/eclevel maxeclevel def} if
    /k 2 eclevel 1 add exp cvi def

    % To determine size of matrix, number of columns if given by user...
    columns 1 ge columns 30 le and {/c columns def} if

    % ... and rows is greater of those required and that given by user within limits
    /r m k add 1 add columns div ceiling cvi def  % Required
    r rows lt rows 90 le and {/r rows def} if
    r 3 lt {/r 3 def} if

    % Opportunistically raise the error level if a better fit to the matrix is possible
    /maxeclevel c r mul 1 sub m sub ln 2 ln div cvi 1 sub def
    maxeclevel eclevel gt {
      /eclevel maxeclevel def
      /k 2 eclevel 1 add exp cvi def
    } if

    % Create codewords array with one extra working space element and add padding
    /n c r mul k sub def
    /cws c r mul 1 add array def
    cws 0 n put
    cws 1 datcws putinterval
    cws m 1 add [ n m sub 1 sub {900} repeat ] putinterval
    cws n [ k {0} repeat 0 ] putinterval

    % Calculate the log and anti-log tables
    /rslog [ -928 928 {0} repeat ] def
    /rsalog [ 1 928 {0} repeat ] def
    1 1 928 {
        /i exch def
        rsalog i rsalog i 1 sub get 3 mul put
        rsalog i get 928 ge { rsalog i rsalog i get 929 mod put } if
        rslog rsalog i get i put
    } for

    % Function to calculate the product in the field
    /rsprod {
        /y exch def
        /x exch def
        x y mul 0 ne { 
            rsalog rslog x get rslog y get add 928 mod get
        } {
            0
        } ifelse
    } bind def

    % Generate the coefficients
    /coeffs [ 1 k {0} repeat ] def
    1 1 k {
        /i exch def 
        coeffs i coeffs i 1 sub get put
        i 1 sub -1 1 {
            /j exch def
            coeffs j coeffs j 1 sub get coeffs j get rsalog i get rsprod add 929 mod put
        } for 
        coeffs 0 coeffs 0 get rsalog i get rsprod put
    } for
    /coeffs coeffs 0 coeffs length 1 sub getinterval def
    1 2 coeffs length 1 sub {coeffs exch 2 copy get 929 exch sub put} for

    % Derive the error codewords
    0 1 n 1 sub {
        /t exch cws exch get cws n get add 929 mod def
        0 1 k 1 sub {
            /j exch def
            cws n j add cws n j add 1 add get 929 t coeffs k j sub 1 sub get mul 929 mod sub add 929 mod put
        } for
    } for
    n 1 n k add { dup cws exch 929 cws 5 -1 roll get sub put } for

    % Trim the working space from the end of the codewords
    /cws cws 0 cws length 1 sub getinterval def

    % Base 10 encoding of the bar space successions for the codewords in each cluster
    /clusters [
        [
            120256 125680 128380 120032 125560 128318 108736 119920 108640  86080 108592  86048
            110016 120560 125820 109792 120440 125758  88256 109680  88160  89536 110320 120700
             89312 110200 120638  89200 110140  89840 110460  89720 110398  89980 128506 119520
            125304 128190 107712 119408 125244 107616 119352  84032 107568 119324  84000 107544
             83984 108256 119672 125374  85184 108144 119612  85088 108088 119582  85040 108060
             85728 108408 119742  85616 108348  85560 108318  85880 108478  85820  85790 107200
            119152 125116 107104 119096 125086  83008 107056 119068  82976 107032  82960  82952
             83648 107376 119228  83552 107320 119198  83504 107292  83480  83468  83824 107452
             83768 107422  83740  83900 106848 118968 125022  82496 106800 118940  82464 106776
            118926  82448 106764  82440 106758  82784 106936 119006  82736 106908  82712 106894
             82700  82694 106974  82830  82240 106672 118876  82208 106648 118862  82192 106636
             82184 106630  82180  82352  82328  82316  82080 118830 106572 106566  82050 117472
            124280 127678 103616 117360 124220 103520 117304 124190  75840 103472  75808 104160
            117624 124350  76992 104048 117564  76896 103992  76848  76824  77536 104312 117694
             77424 104252  77368  77340  77688 104382  77628  77758 121536 126320 128700 121440
            126264 128670 111680 121392 126236 111648 121368 126222 111632 121356 103104 117104
            124092 112320 103008 117048 124062 112224 121656 126366  93248  74784 102936 117006
             93216 112152  93200  75456 103280 117180  93888  75360 103224 117150  93792 112440
            121758  93744  75288  93720  75632 103356  94064  75576 103326  94008 112542  93980
             75708  94140  75678  94110 121184 126136 128606 111168 121136 126108 111136 121112
            126094 111120 121100 111112 111108 102752 116920 123998 111456 102704 116892  91712
             74272 121244 116878  91680  74256 102668  91664 111372 102662  74244  74592 102840
            116958  92000  74544 102812  91952 111516 102798  91928  74508  74502  74680 102878
             92088  74652  92060  74638  92046  92126 110912 121008 126044 110880 120984 126030
            110864 120972 110856 120966 110852 110850  74048 102576 116828  90944  74016 102552
            116814  90912 111000 121038  90896  73992 102534  90888 110982  90884  74160 102620
             91056  74136 102606  91032 111054  91020  74118  91014  91100  91086 110752 120920
            125998 110736 120908 110728 120902 110724 110722  73888 102488 116782  90528  73872
            102476  90512 110796 102470  90504  73860  90500  73858  73944  90584  90572  90566
            120876 120870 110658 102444  73800  90312  90308  90306 101056 116080 123580 100960
            116024  70720 100912 115996  70688 100888  70672  70664  71360 101232 116156  71264
            101176 116126  71216 101148  71192  71180  71536 101308  71480 101278  71452  71612
             71582 118112 124600 127838 105024 118064 124572 104992 118040 124558 104976 118028
            104968 118022 100704 115896 123486 105312 100656 115868  79424  70176 118172 115854
             79392 105240 100620  79376  70152  79368  70496 100792 115934  79712  70448 118238
             79664 105372 100750  79640  70412  79628  70584 100830  79800  70556  79772  70542
             70622  79838 122176 126640 128860 122144 126616 128846 122128 126604 122120 126598
            122116 104768 117936 124508 113472 104736 126684 124494 113440 122264 126670 113424
            104712 117894 113416 122246 104706  69952 100528 115804  78656  69920 100504 115790
             96064  78624 104856 117966  96032 113560 122318 100486  96016  78600 104838  96008
             69890  70064 100572  78768  70040 100558  96176  78744 104910  96152 113614  70022
             78726  70108  78812  70094  96220  78798 122016 126552 128814 122000 126540 121992
            126534 121988 121986 104608 117848 124462 113056 104592 126574 113040 122060 117830
            113032 104580 113028 104578 113026  69792 100440 115758  78240  69776 100428  95136
             78224 104652 100422  95120 113100  69764  95112  78212  69762  78210  69848 100462
             78296  69836  95192  78284  69830  95180  78278  69870  95214 121936 126508 121928
            126502 121924 121922 104528 117804 112848 104520 117798 112840 121958 112836 104514
            112834  69712 100396  78032  69704 100390  94672  78024 104550  94664 112870  69698
             94660  78018  94658  78060  94700  94694 126486 121890 117782 104484 104482  69672
             77928  94440  69666  77922  99680  68160  99632  68128  99608 115342  68112  99596
             68104  99590  68448  99768 115422  68400  99740  68376  99726  68364  68358  68536
             99806  68508  68494  68574 101696 116400 123740 101664 116376 101648 116364 101640
            116358 101636  67904  99504 115292  72512  67872 116444 115278  72480 101784 116430
             72464  67848  99462  72456 101766  67842  68016  99548  72624  67992  99534  72600
            101838  72588  67974  68060  72668  68046  72654 118432 124760 127918 118416 124748
            118408 124742 118404 118402 101536 116312 105888 101520 116300 105872 118476 116294
            105864 101508 105860 101506 105858  67744  99416  72096  67728 116334  80800  72080
            101580  99398  80784 105932  67716  80776  72068  67714  72066  67800  99438  72152
             67788  80856  72140  67782  80844  72134  67822  72174  80878 126800 128940 126792
            128934 126788 126786 118352 124716 122576 126828 124710 122568 126822 122564 118338
            122562 101456 116268 105680 101448 116262 114128 105672 118374 114120 122598 101442
            114116 105666 114114  67664  99372  71888  67656  99366  80336  71880 101478  97232
             80328 105702  67650  97224 114150  71874  97220  67692  71916  67686  80364  71910
             97260  80358  97254 126760 128918 126756 126754 118312 124694 122472 126774 122468
            118306 122466 101416 116246 105576 101412 113896 105572 101410 113892 105570 113890
             67624  99350  71784 101430  80104  71780  67618  96744  80100  71778  96740  80098
             96738  71798  96758 126738 122420 122418 105524 113780 113778  71732  79988  96500
             96498  66880  66848  98968  66832  66824  66820  66992  66968  66956  66950  67036
             67022 100000  99984 115532  99976 115526  99972  99970  66720  98904  69024 100056
             98892  69008 100044  69000 100038  68996  66690  68994  66776  98926  69080 100078
             69068  66758  69062  66798  69102 116560 116552 116548 116546  99920 102096 116588
            115494 102088 116582 102084  99906 102082  66640  68816  66632  98854  73168  68808
             66628  73160  68804  66626  73156  68802  66668  68844  66662  73196  68838  73190
            124840 124836 124834 116520 118632 124854 118628 116514 118626  99880 115478 101992
            116534 106216 101988  99874 106212 101986 106210  66600  98838  68712  99894  72936
             68708  66594  81384  72932  68706  81380  72930  66614  68726  72950  81398 128980
            128978 124820 126900 124818 126898 116500 118580 116498 122740 118578 122738  99860
            101940  99858 106100 101938 114420
        ] [
            128352 129720 125504 128304 129692 125472 128280 129678 125456 128268 125448 128262
            125444 125792 128440 129758 120384 125744 128412 120352 125720 128398 120336 125708
            120328 125702 120324 120672 125880 128478 110144 120624 125852 110112 120600 125838
            110096 120588 110088 120582 110084 110432 120760 125918  89664 110384 120732  89632
            110360 120718  89616 110348  89608 110342  89952 110520 120798  89904 110492  89880
            110478  89868  90040 110558  90012  89998 125248 128176 129628 125216 128152 129614
            125200 128140 125192 128134 125188 125186 119616 125360 128220 119584 125336 128206
            119568 125324 119560 125318 119556 119554 108352 119728 125404 108320 119704 125390
            108304 119692 108296 119686 108292 108290  85824 108464 119772  85792 108440 119758
             85776 108428  85768 108422  85764  85936 108508  85912 108494  85900  85894  85980
             85966 125088 128088 129582 125072 128076 125064 128070 125060 125058 119200 125144
            128110 119184 125132 119176 125126 119172 119170 107424 119256 125166 107408 119244
            107400 119238 107396 107394  83872 107480 119278  83856 107468  83848 107462  83844
             83842  83928 107502  83916  83910  83950 125008 128044 125000 128038 124996 124994
            118992 125036 118984 125030 118980 118978 106960 119020 106952 119014 106948 106946
             82896 106988  82888 106982  82884  82882  82924  82918 124968 128022 124964 124962
            118888 124982 118884 118882 106728 118902 106724 106722  82408 106742  82404  82402
            124948 124946 118836 118834 106612 106610 124224 127664 129372 124192 127640 129358
            124176 127628 124168 127622 124164 124162 117568 124336 127708 117536 124312 127694
            117520 124300 117512 124294 117508 117506 104256 117680 124380 104224 117656 124366
            104208 117644 104200 117638 104196 104194  77632 104368 117724  77600 104344 117710
             77584 104332  77576 104326  77572  77744 104412  77720 104398  77708  77702  77788
             77774 128672 129880  93168 128656 129868  92664 128648 129862  92412 128644 128642
            124064 127576 129326 126368 124048 129902 126352 128716 127558 126344 124036 126340
            124034 126338 117152 124120 127598 121760 117136 124108 121744 126412 124102 121736
            117124 121732 117122 121730 103328 117208 124142 112544 103312 117196 112528 121804
            117190 112520 103300 112516 103298 112514  75680 103384 117230  94112  75664 103372
             94096 112588 103366  94088  75652  94084  75650  75736 103406  94168  75724  94156
             75718  94150  75758 128592 129836  91640 128584 129830  91388 128580  91262 128578
            123984 127532 126160 123976 127526 126152 128614 126148 123970 126146 116944 124012
            121296 116936 124006 121288 126182 121284 116930 121282 102864 116972 111568 102856
            116966 111560 121318 111556 102850 111554  74704 102892  92112  74696 102886  92104
            111590  92100  74690  92098  74732  92140  74726  92134 128552 129814  90876 128548
             90750 128546 123944 127510 126056 128566 126052 123938 126050 116840 123958 121064
            116836 121060 116834 121058 102632 116854 111080 121078 111076 102626 111074  74216
            102646  91112  74212  91108  74210  91106  74230  91126 128532  90494 128530 123924
            126004 123922 126002 116788 120948 116786 120946 102516 110836 102514 110834  73972
             90612  73970  90610 128522 123914 125978 116762 120890 102458 110714 123552 127320
            129198 123536 127308 123528 127302 123524 123522 116128 123608 127342 116112 123596
            116104 123590 116100 116098 101280 116184 123630 101264 116172 101256 116166 101252
            101250  71584 101336 116206  71568 101324  71560 101318  71556  71554  71640 101358
             71628  71622  71662 127824 129452  79352 127816 129446  79100 127812  78974 127810
            123472 127276 124624 123464 127270 124616 127846 124612 123458 124610 115920 123500
            118224 115912 123494 118216 124646 118212 115906 118210 100816 115948 105424 100808
            115942 105416 118246 105412 100802 105410  70608 100844  79824  70600 100838  79816
            105446  79812  70594  79810  70636  79852  70630  79846 129960  95728 113404 129956
             95480 113278 129954  95356  95294 127784 129430  78588 128872 129974  95996  78462
            128868 127778  95870 128866 123432 127254 124520 123428 126696 128886 123426 126692
            124514 126690 115816 123446 117992 115812 122344 117988 115810 122340 117986 122338
            100584 115830 104936 100580 113640 104932 100578 113636 104930 113634  70120 100598
             78824  70116  96232  78820  70114  96228  78818  96226  70134  78838 129940  94968
            113022 129938  94844  94782 127764  78206 128820 127762  95102 128818 123412 124468
            123410 126580 124466 126578 115764 117876 115762 122100 117874 122098 100468 104692
            100466 113140 104690 113138  69876  78324  69874  95220  78322  95218 129930  94588
             94526 127754 128794 123402 124442 126522 115738 117818 121978 100410 104570 112890
             69754  78074  94714  94398 123216 127148 123208 127142 123204 123202 115408 123244
            115400 123238 115396 115394  99792 115436  99784 115430  99780  99778  68560  99820
             68552  99814  68548  68546  68588  68582 127400 129238  72444 127396  72318 127394
            123176 127126 123752 123172 123748 123170 123746 115304 123190 116456 115300 116452
            115298 116450  99560 115318 101864  99556 101860  99554 101858  68072  99574  72680
             68068  72676  68066  72674  68086  72694 129492  80632 105854 129490  80508  80446
            127380  72062 127924 127378  80766 127922 123156 123700 123154 124788 123698 124786
            115252 116340 115250 118516 116338 118514  99444 101620  99442 105972 101618 105970
             67828  72180  67826  80884  72178  80882  97008 114044  96888 113982  96828  96798
            129482  80252 130010  97148  80190  97086 127370 127898 128954 123146 123674 124730
            126842 115226 116282 118394 122618  99386 101498 105722 114170  67706  71930  80378
             96632 113854  96572  96542  80062  96702  96444  96414  96350 123048 123044 123042
            115048 123062 115044 115042  99048 115062  99044  99042  67048  99062  67044  67042
             67062 127188  68990 127186 123028 123316 123026 123314 114996 115572 114994 115570
             98932 100084  98930 100082  66804  69108  66802  69106 129258  73084  73022 127178
            127450 123018 123290 123834 114970 115514 116602  98874  99962 102138  66682  68858
             73210  81272 106174  81212  81182  72894  81342  97648 114364  97592 114334  97564
             97550  81084  97724  81054  97694  97464 114270  97436  97422  80990  97502  97372
             97358  97326 114868 114866  98676  98674  66292  66290 123098 114842 115130  98618
             99194  66170  67322  69310  73404  73374  81592 106334  81564  81550  73310  81630
             97968 114524  97944 114510  97932  97926  81500  98012  81486  97998  97880 114478
             97868  97862  81454  97902  97836  97830  69470  73564  73550  81752 106414  81740
             81734  73518  81774  81708  81702
        ] [
            109536 120312  86976 109040 120060  86496 108792 119934  86256 108668  86136 129744
             89056 110072 129736  88560 109820 129732  88312 109694 129730  88188 128464 129772
             89592 128456 129766  89340 128452  89214 128450 125904 128492 125896 128486 125892
            125890 120784 125932 120776 125926 120772 120770 110544 120812 110536 120806 110532
             84928 108016 119548  84448 107768 119422  84208 107644  84088 107582  84028 129640
             85488 108284 129636  85240 108158 129634  85116  85054 128232 129654  85756 128228
             85630 128226 125416 128246 125412 125410 119784 125430 119780 119778 108520 119798
            108516 108514  83424 107256 119166  83184 107132  83064 107070  83004  82974 129588
             83704 107390 129586  83580  83518 128116  83838 128114 125172 125170 119284 119282
            107508 107506  82672 106876  82552 106814  82492  82462 129562  82812  82750 128058
            125050 119034  82296 106686  82236  82206  82366  82108  82078  76736 103920 117500
             76256 103672 117374  76016 103548  75896 103486  75836 129384  77296 104188 129380
             77048 104062 129378  76924  76862 127720 129398  77564 127716  77438 127714 124392
            127734 124388 124386 117736 124406 117732 117730 104424 117750 104420 104418 112096
            121592 126334  92608 111856 121468  92384 111736 121406  92272 111676  92216 111646
             92188  75232 103160 117118  93664  74992 103036  93424 112252 102974  93304  74812
             93244  74782  93214 129332  75512 103294 129908 129330  93944  75388 129906  93820
             75326  93758 127604  75646 128756 127602  94078 128754 124148 126452 124146 126450
            117236 121844 117234 121842 103412 103410  91584 111344 121212  91360 111224 121150
             91248 111164  91192 111134  91164  91150  74480 102780  91888  74360 102718  91768
            111422  91708  74270  91678 129306  74620 129850  92028  74558  91966 127546 128634
            124026 126202 116986 121338 102906  90848 110968 121022  90736 110908  90680 110878
             90652  90638  74104 102590  91000  74044  90940  74014  90910  74174  91070  90480
            110780  90424 110750  90396  90382  73916  90556  73886  90526  90296 110686  90268
             90254  73822  90334  90204  90190  71136 101112 116094  70896 100988  70776 100926
             70716  70686 129204  71416 101246 129202  71292  71230 127348  71550 127346 123636
            123634 116212 116210 101364 101362  79296 105200 118140  79072 105080 118078  78960
            105020  78904 104990  78876  78862  70384 100732  79600  70264 100670  79480 105278
             79420  70174  79390 129178  70524 129466  79740  70462  79678 127290 127866 123514
            124666 115962 118266 100858 113376 122232 126654  95424 113264 122172  95328 113208
            122142  95280 113180  95256 113166  95244  78560 104824 117950  95968  78448 104764
             95856 113468 104734  95800  78364  95772  78350  95758  70008 100542  78712  69948
             96120  78652  69918  96060  78622  96030  70078  78782  96190  94912 113008 122044
             94816 112952 122014  94768 112924  94744 112910  94732  94726  78192 104636  95088
             78136 104606  95032 113054  95004  78094  94990  69820  78268  69790  95164  78238
             95134  94560 112824 121950  94512 112796  94488 112782  94476  94470  78008 104542
             94648  77980  94620  77966  94606  69726  78046  94686  94384 112732  94360 112718
             94348  94342  77916  94428  77902  94414  94296 112686  94284  94278  77870  94318
             94252  94246  68336  99708  68216  99646  68156  68126  68476  68414 127162 123258
            115450  99834  72416 101752 116414  72304 101692  72248 101662  72220  72206  67960
             99518  72568  67900  72508  67870  72478  68030  72638  80576 105840 118460  80480
            105784 118430  80432 105756  80408 105742  80396  80390  72048 101564  80752  71992
            101534  80696  71964  80668  71950  80654  67772  72124  67742  80828  72094  80798
            114016 122552 126814  96832 113968 122524  96800 113944 122510  96784 113932  96776
            113926  96772  80224 105656 118366  97120  80176 105628  97072 114076 105614  97048
             80140  97036  80134  97030  71864 101470  80312  71836  97208  80284  71822  97180
             80270  97166  67678  71902  80350  97246  96576 113840 122460  96544 113816 122446
             96528 113804  96520 113798  96516  96514  80048 105564  96688  80024 105550  96664
            113870  96652  80006  96646  71772  80092  71758  96732  80078  96718  96416 113752
            122414  96400 113740  96392 113734  96388  96386  79960 105518  96472  79948  96460
             79942  96454  71726  79982  96494  96336 113708  96328 113702  96324  96322  79916
             96364  79910  96358  96296 113686  96292  96290  79894  96310  66936  99006  66876
             66846  67006  68976 100028  68920  99998  68892  68878  66748  69052  66718  69022
             73056 102072 116574  73008 102044  72984 102030  72972  72966  68792  99934  73144
             68764  73116  68750  73102  66654  68830  73182  81216 106160 118620  81184 106136
            118606  81168 106124  81160 106118  81156  81154  72880 101980  81328  72856 101966
             81304 106190  81292  72838  81286  68700  72924  68686  81372  72910  81358 114336
            122712 126894 114320 122700 114312 122694 114308 114306  81056 106072 118574  97696
             81040 106060  97680 114380 106054  97672  81028  97668  81026  97666  72792 101934
             81112  72780  97752  81100  72774  97740  81094  97734  68654  72814  81134  97774
            114256 122668 114248 122662 114244 114242  80976 106028  97488  80968 106022  97480
            114278  97476  80962  97474  72748  81004  72742  97516  80998  97510 114216 122646
            114212 114210  80936 106006  97384  80932  97380  80930  97378  72726  80950  97398
            114196 114194  80916  97332  80914  97330  66236  66206  67256  99166  67228  67214
             66142  67294  69296 100188  69272 100174  69260  69254  67164  69340  67150  69326
             73376 102232 116654  73360 102220  73352 102214  73348  73346  69208 100142  73432
            102254  73420  69190  73414  67118  69230  73454 106320 118700 106312 118694 106308
            106306  73296 102188  81616 106348 102182  81608  73284  81604  73282  81602  69164
             73324  69158  81644  73318  81638 122792 126934 122788 122786 106280 118678 114536
            106276 114532 106274 114530  73256 102166  81512  73252  98024  81508  73250  98020
             81506  98018  69142  73270  81526  98038 122772 122770 106260 114484 106258 114482
             73236  81460  73234  97908  81458  97906 122762 106250 114458  73226  81434  97850
             66396  66382  67416  99246  67404  67398  66350  67438  69456 100268  69448 100262
             69444  69442  67372  69484  67366  69478 102312 116694 102308 102306  69416 100246
             73576 102326  73572  69410  73570  67350  69430  73590 118740 118738 102292 106420
            102290 106418  69396  73524  69394  81780  73522  81778 118730 102282 106394  69386
             73498  81722  66476  66470  67496  99286  67492  67490  66454  67510 100308 100306
             67476  69556  67474  69554 116714
        ]
    ] def

    % Return the 17 bits for a codeword in a given cluster
    /cwtobits {
        clusters exch get exch get /v exch def
        [ 17 {0} repeat v 2 17 string cvrs {48 sub} forall ]
        dup length 17 sub 17 getinterval
    } bind def

    % Populate bitmap for the image
    compact {
        /rwid 17 c mul 17 add 17 add 1 add def
    } {
        /rwid 17 c mul 17 add 17 add 17 add 18 add def
    } ifelse
    /pixs rwid r mul array def

   0 1 r 1 sub {
        /i exch def

        i 3 mod 0 eq {
            /lcw i 3 idiv 30 mul r 1 sub 3 idiv add def
            /rcw i 3 idiv 30 mul c add 1 sub def
        } if
        i 3 mod 1 eq {
            /lcw i 3 idiv 30 mul eclevel 3 mul add r 1 sub 3 mod add def
            /rcw i 3 idiv 30 mul r 1 sub 3 idiv add def
        } if
        i 3 mod 2 eq {
            /lcw i 3 idiv 30 mul c add 1 sub def
            /rcw i 3 idiv 30 mul eclevel 3 mul add r 1 sub 3 mod add def
        } if

        pixs rwid i mul [
            1 1 1 1 1 1 1 1 0 1 0 1 0 1 0 0 0
            lcw i 3 mod cwtobits {} forall
            cws c i mul c getinterval { i 3 mod cwtobits {} forall } forall
            compact {
                1
            } {
                rcw i 3 mod cwtobits {} forall
                1 1 1 1 1 1 1 0 1 0 0 0 1 0 1 0 0 1
            } ifelse
        ] putinterval

    } for

    /retval 7 dict def
    retval (ren) (renmatrix) put
    retval (pixs) pixs put
    retval (pixx) rwid put
    retval (pixy) r put
    retval (height) r 72 div rowmult mul put
    retval (width) rwid 72 div put
    retval (opt) useropts put
    retval

    end

} bind def
/pdf417 load 0 1 dict put
% --END ENCODER pdf417--

% --BEGIN ENCODER datamatrix--
% --DESC: Data Matrix
% --EXAM: ^142^164^186
% --EXOP: rows=32 columns=32
% --RNDR: renmatrix
/datamatrix {

    0 begin

    /options exch def
    /useropts options def
    /barcode exch def

    /columns 0 def
    /rows 0 def

    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop

    /columns columns cvi def
    /rows rows cvi def

    % Split the input barcode into an array of codewords
    /cws barcode length array def
    /i 0 def /j 0 def
    { % loop
        i barcode length eq {exit} if
        /cw barcode i 1 add 3 getinterval cvi def
        cws j cw put
        /i i 4 add def
        /j j 1 add def
    } loop
    /cws cws 0 j getinterval def

    % Basic metrics for the each symbol
    %    rows  cols  regh  regv  rscw  rsbl
    /metrics [
        % Standard square symbols
        [  10    10     1     1     5     1 ]
        [  12    12     1     1     7     1 ]
        [  14    14     1     1    10     1 ]
        [  16    16     1     1    12     1 ]
        [  18    18     1     1    14     1 ]
        [  20    20     1     1    18     1 ] 
        [  22    22     1     1    20     1 ]
        [  24    24     1     1    24     1 ]
        [  26    26     1     1    28     1 ]
        [  32    32     2     2    36     1 ]
        [  36    36     2     2    42     1 ]
        [  40    40     2     2    48     1 ]
        [  44    44     2     2    56     1 ]
        [  48    48     2     2    68     1 ]
        [  52    52     2     2    84     2 ]
        [  64    64     4     4   112     2 ]
        [  72    72     4     4   144     4 ]
        [  80    80     4     4   192     4 ]
        [  88    88     4     4   224     4 ]
        [  96    96     4     4   272     4 ]
        [ 104   104     4     4   336     6 ]
        [ 120   120     6     6   408     6 ]
        [ 132   132     6     6   496     8 ]
        [ 144   144     6     6   620    10 ]
        % Optional rectangular symbols
        [   8    18     1     1     7     1 ]
        [   8    32     1     2    11     1 ]
        [  12    26     1     1    14     1 ]
        [  12    36     1     2    18     1 ]
        [  16    36     1     2    24     1 ]
        [  16    48     1     2    28     1 ]
    ] def

    % Select metrics of an appropriate symbol
    /urows rows def
    /ucols columns def
    /i 0 def
    { % loop
        /m metrics i get def
        /rows m 0 get def                          % Rows in symbol
        /cols m 1 get def                          % Columns in symbol
        /regh m 2 get def                          % Horizontal regions
        /regv m 3 get def                          % Vertical regions
        /rscw m 4 get def                          % Error correction codewords
        /rsbl m 5 get def                          % Error correction blocks
        /mrows rows 2 regh mul sub def             % Rows in the mapping matrix
        /mcols cols 2 regv mul sub def             % Columns in the mapping matrix
        /rrows mrows regh idiv def                 % Rows per region
        /rcols mcols regv idiv def                 % Columns per region
        /ncws mrows mcols mul 8 idiv rscw sub def  % Data codewords
        /okay true def
        cws length ncws gt           {/okay false def} if
        urows 0 ne urows rows ne and {/okay false def} if
        ucols 0 ne ucols cols ne and {/okay false def} if
        okay {exit} if
        /i i 1 add def
    } loop

    % Extend cws to ncws codewords by addition of pseudo-randomised pad characters
    cws length ncws lt {
        /datlen cws length def
        /cws [ cws {} forall ncws datlen sub {129} repeat ] def
        datlen 1 add 1 ncws 1 sub {
            /i exch def
            i 1 add 149 mul 253 mod 1 add 129 add
            dup 254 gt {254 sub} if
            cws exch i exch put
        } for
    } if

    % De-interleave the codewords into blocks
    /cwbs rsbl array def  % Array of data codeword blocks
    /ecbs rsbl array def  % Array of error correction blocks
    0 1 rsbl 1 sub {
        /i exch def
        cws length 1558 ne {
            /cwbsize cws length rsbl idiv def
        } {
            i 7 le {/cwbsize 156 def} {/cwbsize 155 def} ifelse
        } ifelse
        /cwb cwbsize array def 
        0 1 cwbsize 1 sub {
            /j exch def
            cwb j cws j rsbl mul i add get put
        } for 
        cwbs i cwb put
        ecbs i [ rscw rsbl idiv {0} repeat ] put
    } for

    % Calculate the log and anti-log tables
    /rslog [ -255 255 {0} repeat ] def
    /rsalog [ 1 255 {0} repeat ] def
    1 1 255 {
        /i exch def
        rsalog i rsalog i 1 sub get 2 mul put
        rsalog i get 256 ge { rsalog i rsalog i get 301 xor put } if
        rslog rsalog i get i put
    } for

    % Function to calculate the product in the field
    /rsprod {
        /y exch def
        /x exch def
        x y mul 0 ne { 
            rsalog rslog x get rslog y get add 255 mod get
        } {
            0
        } ifelse
    } bind def

    % Generate the coefficients
    /coeffs [ 1 rscw rsbl idiv {0} repeat ] def
    1 1 rscw rsbl idiv {
        /i exch def 
        coeffs i coeffs i 1 sub get put
        i 1 sub -1 1 {
            /j exch def
            coeffs j coeffs j 1 sub get coeffs j get rsalog i get rsprod xor put
        } for 
        coeffs 0 coeffs 0 get rsalog i get rsprod put
    } for
    /coeffs coeffs 0 coeffs length 1 sub getinterval def

    % Calculate the error correction codewords for each block
    0 1 cwbs length 1 sub {
        /i exch def
        /cwb cwbs i get def
        /ecb ecbs i get def
        0 1 cwb length 1 sub {
            /t exch cwb exch get ecb 0 get xor def 
            ecb length 1 sub -1 0 {
                /j exch def
                /p ecb length j sub 1 sub def
                t 0 eq {
                    ecb p 0 put
                } {
                    ecb p rsalog rslog t get rslog coeffs j get get add 255 mod get put
                } ifelse
                j 0 gt { ecb p ecb p 1 add get ecb p get xor put } if
            } for 
        } for
        ecbs i ecb put
    } for

    % Extend codewords with the interleaved error correction codes
    /cws [ cws {} forall rscw {0} repeat ] def
    0 1 rscw 1 sub {
        /i exch def
        cws ncws i add ecbs i rsbl mod get i rsbl idiv get put
    } for

    % Create the module placement matrix
    /module {
        /tmpc exch def
        /tmpr exch def
        tmpr 0 lt {  
            /tmpr tmpr mrows add def
            /tmpc tmpc 4 mrows 4 add 8 mod sub add def
        } if
        tmpc 0 lt { 
            /tmpc tmpc mcols add def
            /tmpr tmpr 4 mcols 4 add 8 mod sub add def
        } if
        mmat tmpr mcols mul tmpc add bit put
        /bit bit 1 add def
    } bind def

    /mmat [ mrows mcols mul {-1} repeat ] def
    /bit 0 def /row 4 def /col 0 def
    { % loop

        row mrows eq col 0 eq and {
            [ [mrows 1 sub 0] [mrows 1 sub 1] [mrows 1 sub 2] [0 mcols 2 sub]
              [0 mcols 1 sub] [1 mcols 1 sub] [2 mcols 1 sub] [3 mcols 1 sub] ]
            {{} forall module} forall 
        } if
        row mrows 2 sub eq col 0 eq and mcols 4 mod 0 ne and {
            [ [mrows 3 sub 0] [mrows 2 sub 0] [mrows 1 sub 0] [0 mcols 4 sub]
              [0 mcols 3 sub] [0 mcols 2 sub] [0 mcols 1 sub] [1 mcols 1 sub] ]
            {{} forall module} forall
        } if
        row mrows 2 sub eq col 0 eq and mcols 8 mod 4 eq and {
            [ [mrows 3 sub 0] [mrows 2 sub 0] [mrows 1 sub 0] [0 mcols 2 sub]
              [0 mcols 1 sub] [1 mcols 1 sub] [2 mcols 1 sub] [3 mcols 1 sub] ]
            {{} forall module} forall
        } if
        row mrows 4 add eq col 2 eq and mcols 8 mod 0 eq and {
            [ [mrows 1 sub 0] [mrows 1 sub mcols 1 sub] [0 mcols 3 sub] [0 mcols 2 sub]
              [0 mcols 1 sub] [1 mcols 3 sub]           [1 mcols 2 sub] [1 mcols 1 sub] ]
            {{} forall module} forall
        } if

        { % loop for sweeping upwards
            row mrows lt col 0 ge and {
                mmat row mcols mul col add get -1 eq {
                    [ [row 2 sub col 2 sub] [row 2 sub col 1 sub] [row 1 sub col 2 sub] [row 1 sub col 1 sub]
                      [row 1 sub col]       [row col 2 sub]       [row col 1 sub]       [row col] ]
                    {{} forall module} forall
                } if
            } if
            /row row 2 sub def
            /col col 2 add def
            row 0 ge col mcols lt and not {exit} if
        } loop
        /row row 1 add def
        /col col 3 add def

        { % loop for sweeping downwards
            row 0 ge col mcols lt and {
                mmat row mcols mul col add get -1 eq {
                    [ [row 2 sub col 2 sub] [row 2 sub col 1 sub] [row 1 sub col 2 sub] [row 1 sub col 1 sub]
                      [row 1 sub col]       [row col 2 sub]       [row col 1 sub]       [row col] ]
                    {{} forall module} forall
                } if
            } if
            /row row 2 add def
            /col col 2 sub def
            row mrows lt col 0 ge and not {exit} if
        } loop
        /row row 3 add def
        /col col 1 add def

        row mrows lt col mcols lt or not {exit} if
    } loop

    % Set checker pattern if required
    mmat mrows mcols mul 1 sub get -1 eq {
        mmat mrows mcols 1 sub mul 2 sub [-1 -2] putinterval
        mmat mrows mcols mul 2 sub [-2 -1] putinterval
    } if

    % Invert the map to form the mapping matrix correcting the checker case
    /modmap mrows mcols mul 8 idiv 8 mul array def
    0 1 mmat length 1 sub {
        /i exch def
        mmat i get 0 ge {
            modmap mmat i get i put
        } {
            mmat i mmat i get 2 add put
        } ifelse
    } for

    % Place the codewords in the matrix according to the mapping matrix
    0 1 cws length 1 sub {
        /i exch def
        [ 8 {0} repeat cws i get 2 8 string cvrs {48 sub} forall ]
        dup length 8 sub 8 getinterval /bits exch def
        0 1 7 {
            /j exch def
            mmat modmap i 8 mul j add get bits j get put
        } for
    } for

    % Place the modules onto a pixel map between alignment patterns
    /pixs rows cols mul array def
    /cwpos 0 def
    0 1 rows 1 sub {
        /i exch def
        i rrows 2 add mod 0 eq { pixs i cols mul [ cols 2 idiv {1 0} repeat ] putinterval } if  
        i rrows 2 add mod rrows 1 add eq { pixs i cols mul [ cols {1} repeat ] putinterval } if 
        i rrows 2 add mod 0 ne i rrows 2 add mod rrows 1 add ne and {
            0 1 cols 1 sub {
                /j exch def
                j rcols 2 add mod 0 eq { pixs i cols mul j add 1 put } if
                j rcols 2 add mod rcols 1 add eq { pixs i cols mul j add i 2 mod put } if
                j rcols 2 add mod 0 ne j rcols 2 add mod rcols 1 add ne and {
                    pixs i cols mul j add mmat cwpos get put
                    /cwpos cwpos 1 add def
                } if
            } for
        } if 
    } for

    /retval 7 dict def
    retval (ren) (renmatrix) put
    retval (pixs) pixs put
    retval (pixx) cols put
    retval (pixy) rows put
    retval (height) rows 72 div 1.5 mul put
    retval (width) cols 72 div 1.5 mul put
    retval (opt) useropts put
    retval

    end

} bind def
/datamatrix load 0 1 dict put
% --END ENCODER datamatrix--

% --BEGIN ENCODER qrcode--
% --DESC: QR Code
% --EXAM: 000100000010000000001100010101100110000110000
% --EXOP: version=1 eclevel=M
% --RNDR: renmatrix
/qrcode {

    0 begin

    /options exch def
    /useropts options def
    /barcode exch def

    /format (full) def     % full or micro
    /version (unset) def
    /eclevel (L) def       % L, M, Q or H

    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop

    % Convert from input into message bitstream
    /msgbits barcode def 

    % Lookup the most appropriate symbol specification
    /metrics [
        % format   vers  size align modules    error codewords        error correction blocks 
        %                                      L    M    Q    H       L1 L2 M1 M2 Q1 Q2 H1 H2
        [ (micro)  (M1)   11  98 99     36  [   2   99   99   99 ]  [  1  0 99 99 99 99 99 99 ] ]
        [ (micro)  (M2)   13  98 99     80  [   5    6   99   99 ]  [  1  0  1  0 99 99 99 99 ] ]
        [ (micro)  (M3)   15  98 99    132  [   6    8   99   99 ]  [  1  0  1  0 99 99 99 99 ] ]
        [ (micro)  (M4)   17  98 99    192  [   8   10   14   99 ]  [  1  0  1  0  1  0 99 99 ] ]
        [ (full)   (1)    21  98 99    208  [   7   10   13   17 ]  [  1  0  1  0  1  0  1  0 ] ]
        [ (full)   (2)    25  18 99    359  [  10   16   22   28 ]  [  1  0  1  0  1  0  1  0 ] ]
        [ (full)   (3)    29  22 99    567  [  15   26   36   44 ]  [  1  0  1  0  2  0  2  0 ] ]
        [ (full)   (4)    33  26 99    807  [  20   36   52   64 ]  [  1  0  2  0  2  0  4  0 ] ]
        [ (full)   (5)    37  30 99   1079  [  26   48   72   88 ]  [  1  0  2  0  2  2  2  2 ] ]
        [ (full)   (6)    41  34 99   1383  [  36   64   96  112 ]  [  2  0  4  0  4  0  4  0 ] ]
        [ (full)   (7)    45  22 38   1568  [  40   72  108  130 ]  [  2  0  4  0  2  4  4  1 ] ]
        [ (full)   (8)    49  24 42   1936  [  48   88  132  156 ]  [  2  0  2  2  4  2  4  2 ] ]
        [ (full)   (9)    53  26 46   2336  [  60  110  160  192 ]  [  2  0  3  2  4  4  4  4 ] ]
        [ (full)   (10)   57  28 50   2768  [  72  130  192  224 ]  [  2  2  4  1  6  2  6  2 ] ]
        [ (full)   (11)   61  30 54   3232  [  80  150  224  264 ]  [  4  0  1  4  4  4  3  8 ] ]
        [ (full)   (12)   65  32 58   3728  [  96  176  260  308 ]  [  2  2  6  2  4  6  7  4 ] ]
        [ (full)   (13)   69  34 62   4256  [ 104  198  288  352 ]  [  4  0  8  1  8  4 12  4 ] ]
        [ (full)   (14)   73  26 46   4651  [ 120  216  320  384 ]  [  3  1  4  5 11  5 11  5 ] ]
        [ (full)   (15)   77  26 48   5243  [ 132  240  360  432 ]  [  5  1  5  5  5  7 11  7 ] ]
        [ (full)   (16)   81  26 50   5867  [ 144  280  408  480 ]  [  5  1  7  3 15  2  3 13 ] ]
        [ (full)   (17)   85  30 54   6523  [ 168  308  448  532 ]  [  1  5 10  1  1 15  2 17 ] ]
        [ (full)   (18)   89  30 56   7211  [ 180  338  504  588 ]  [  5  1  9  4 17  1  2 19 ] ]
        [ (full)   (19)   93  30 58   7931  [ 196  364  546  650 ]  [  3  4  3 11 17  4  9 16 ] ]
        [ (full)   (20)   97  34 62   8683  [ 224  416  600  700 ]  [  3  5  3 13 15  5 15 10 ] ]
        [ (full)   (21)  101  28 50   9252  [ 224  442  644  750 ]  [  4  4 17  0 17  6 19  6 ] ]
        [ (full)   (22)  105  26 50  10068  [ 252  476  690  816 ]  [  2  7 17  0  7 16 34  0 ] ]
        [ (full)   (23)  109  30 54  10916  [ 270  504  750  900 ]  [  4  5  4 14 11 14 16 14 ] ]
        [ (full)   (24)  113  28 54  11796  [ 300  560  810  960 ]  [  6  4  6 14 11 16 30  2 ] ]
        [ (full)   (25)  117  32 58  12708  [ 312  588  870 1050 ]  [  8  4  8 13  7 22 22 13 ] ]
        [ (full)   (26)  121  30 58  13652  [ 336  644  952 1110 ]  [ 10  2 19  4 28  6 33  4 ] ]
        [ (full)   (27)  125  34 62  14628  [ 360  700 1020 1200 ]  [  8  4 22  3  8 26 12 28 ] ]
        [ (full)   (28)  129  26 50  15371  [ 390  728 1050 1260 ]  [  3 10  3 23  4 31 11 31 ] ]
        [ (full)   (29)  133  30 54  16411  [ 420  784 1140 1350 ]  [  7  7 21  7  1 37 19 26 ] ]
        [ (full)   (30)  137  26 52  17483  [ 450  812 1200 1440 ]  [  5 10 19 10 15 25 23 25 ] ]
        [ (full)   (31)  141  30 56  18587  [ 480  868 1290 1530 ]  [ 13  3  2 29 42  1 23 28 ] ]
        [ (full)   (32)  145  34 60  19723  [ 510  924 1350 1620 ]  [ 17  0 10 23 10 35 19 35 ] ]
        [ (full)   (33)  149  30 58  20891  [ 540  980 1440 1710 ]  [ 17  1 14 21 29 19 11 46 ] ]
        [ (full)   (34)  153  34 62  22091  [ 570 1036 1530 1800 ]  [ 13  6 14 23 44  7 59  1 ] ]
        [ (full)   (35)  157  30 54  23008  [ 570 1064 1590 1890 ]  [ 12  7 12 26 39 14 22 41 ] ]
        [ (full)   (36)  161  24 50  24272  [ 600 1120 1680 1980 ]  [  6 14  6 34 46 10  2 64 ] ]
        [ (full)   (37)  165  28 54  25568  [ 630 1204 1770 2100 ]  [ 17  4 29 14 49 10 24 46 ] ]
        [ (full)   (38)  169  32 58  26896  [ 660 1260 1860 2220 ]  [  4 18 13 32 48 14 42 32 ] ]
        [ (full)   (39)  173  26 54  28256  [ 720 1316 1950 2310 ]  [ 20  4 40  7 43 22 10 67 ] ]
        [ (full)   (40)  177  30 58  29648  [ 750 1372 2040 2430 ]  [ 19  6 18 31 34 34 20 61 ] ]
    ] def

    /eclval (LMQH) eclevel search pop length exch pop exch pop def
    /i 0 def
    { % loop
        /m metrics i get def
        /frmt m 0 get def                             % Format of the symbol
        /vers m 1 get def                             % Version of symbol
        /size m 2 get def                             % Length of side
        /asp2 m 3 get def                             % Position of second alignment symbol
        /asp3 m 4 get def                             % Position of third alignment symbol
        /nmod m 5 get def                             % Number of modules
        /ncws nmod 8 idiv def                         % Total number of codewords
        /rbit nmod 8 mod def                          % Number of remainder bits
        /lc4b false def                               % Last data codeword is 4 bits long
        size 11 eq size 15 eq or {                    % Adjustments for M1 and M3 symbols
            /ncws ncws 1 add def
            /rbit 0 def
            /lc4b true def
        } if
        /ecws m 6 get eclval get def                  % Number of error correction codewords
        /dcws ncws ecws sub def                       % Number of data codewords
        /dmod dcws 8 mul lc4b {4} {0} ifelse sub def  % Number of data modules
        /ecb1 m 7 get eclval 2 mul get def            % First error correction blocks
        /ecb2 m 7 get eclval 2 mul 1 add get def      % Second error correction blocks
        /dcpb dcws ecb1 ecb2 add idiv def             % Base data codewords per block
        /ecpb ncws ecb1 ecb2 add idiv dcpb sub def    % Error correction codewords per block
        /okay true def
        version (unset) ne version vers ne and {/okay false def} if
        version (unset) eq format frmt ne and {/okay false def} if
        msgbits length dmod gt {/okay false def} if
        okay {exit} if
        /i i 1 add def
    } loop
    /format frmt def
    /version vers def

    % Expand the message bits by adding padding as necessary
    /pad dmod string def
    0 4 dmod 1 sub {pad exch (0000) putinterval} for
    pad 0 msgbits putinterval
    /padstrs [ (11101100) (00010001) ] def
    /padnum 0 def
    msgbits length 8 div ceiling 8 mul cvi 8 dmod lc4b {5} {1} ifelse sub {
        pad exch padstrs padnum get putinterval 
        /padnum padnum 1 add 2 mod def
    } for

    % Evaluate the padded message into codewords
    /cws dcws array def 
    0 1 cws length 1 sub {
        /c exch def
        /bpcw 8 def
        lc4b c cws length 1 sub eq and {/bpcw 4 def} if
        /cwb pad c 8 mul bpcw getinterval def
        /cw 0 def
        0 1 bpcw 1 sub {
            /i exch def
            /cw cw 2 bpcw i sub 1 sub exp cvi cwb i get 48 sub mul add def
        } for 
        cws c cw put
    } for 

    % Calculate the log and anti-log tables
    /rslog [ -255 255 {0} repeat ] def
    /rsalog [ 1 255 {0} repeat ] def
    1 1 255 {
        /i exch def
        rsalog i rsalog i 1 sub get 2 mul put
        rsalog i get 256 ge { rsalog i rsalog i get 285 xor put } if 
        rslog rsalog i get i put 
    } for

    % Function to calculate the product in the field
    /rsprod {
        /y exch def
        /x exch def
        x y mul 0 ne { 
            rsalog rslog x get rslog y get add 255 mod get
        } {
            0
        } ifelse
    } bind def

    % Generate the coefficients for the Reed-Solomon algorithm
    /coeffs [ 1 ecpb {0} repeat ] def
    0 1 ecpb 1 sub {
        /i exch def 
        coeffs i 1 add coeffs i get put
        i -1 1 {
            /j exch def
            coeffs j coeffs j 1 sub get coeffs j get rsalog i get rsprod xor put
        } for 
        coeffs 0 coeffs 0 get rsalog i get rsprod put
    } for
    /coeffs coeffs 0 coeffs length 1 sub getinterval def

    % Reed-Solomon algorithm to derive the error correction codewords
    /rscodes {
        /rscws exch def
        /rsnd rscws length def
        /rscws [ rscws {} forall ecpb {0} repeat ] def
        0 1 rsnd 1 sub {
            /m exch def
            /k rscws m get def
            0 1 ecpb 1 sub {
                /j exch def
                rscws m j add 1 add coeffs ecpb j sub 1 sub get k rsprod rscws m j add 1 add get xor put
            } for
        } for
        rscws rsnd ecpb getinterval
    } bind def

    % Divide codewords into two groups of blocks and calculate the error correction codewords
    /dcwsb ecb1 ecb2 add array def
    /ecwsb ecb1 ecb2 add array def
    0 1 ecb1 1 sub {  % First group of blocks has smaller number of data codewords
        /i exch def
        dcwsb i cws i dcpb mul dcpb getinterval put
        ecwsb i dcwsb i get rscodes put
    } for
    0 1 ecb2 1 sub {  % Second group of blocks has larger number of data codewords
        /i exch def
        dcwsb ecb1 i add cws ecb1 dcpb mul i dcpb 1 add mul add dcpb 1 add getinterval put
        ecwsb ecb1 i add dcwsb ecb1 i add get rscodes put
    } for
    
    % Reassemble the codewords
    /cws ncws array def
    /cw 0 def
    0 1 dcpb {  % Interleave the data codeword blocks
        /i exch def
        0 1 ecb1 ecb2 add 1 sub {
            /j exch def
            i dcwsb j get length lt {  % Ignore the end of short blocks
                cws cw dcwsb j get i get put
                /cw cw 1 add def
            } if
        } for
    } for
    0 1 ecpb 1 sub {  % Interleave the error codeword blocks
        /i exch def
        0 1 ecb1 ecb2 add 1 sub {
            /j exch def
            cws cw ecwsb j get i get put
            /cw cw 1 add def
        } for
    } for
    
    % Extend codewords by one if there are remainder bits
    rbit 0 gt {
        /pad cws length 1 add array def
        pad 0 cws putinterval
        pad pad length 1 sub 0 put
        /cws pad def
    } if
 
    % Fixups for the short final data byte in M1 and M3 symbols
    lc4b {
        dcws 1 sub 1 ncws 2 sub {
            /i exch def
            cws i cws i get 15 and 4 bitshift put
            cws i cws i 1 add get -4 bitshift 15 and cws i get or put
        } for
        cws ncws 1 sub cws ncws 1 sub get 15 and 4 bitshift put
    } if

    % Create the bitmap
    /pixs [ size size mul {-1} repeat ] def
    /qmv {size mul add} bind def
    
    % Finder patterns
    /fpat [
        [ 1 1 1 1 1 1 1 0 ]
        [ 1 0 0 0 0 0 1 0 ]
        [ 1 0 1 1 1 0 1 0 ]
        [ 1 0 1 1 1 0 1 0 ]
        [ 1 0 1 1 1 0 1 0 ]
        [ 1 0 0 0 0 0 1 0 ]
        [ 1 1 1 1 1 1 1 0 ]
        [ 0 0 0 0 0 0 0 0 ]
    ] def
    0 1 fpat length 1 sub {
      /y exch def
      0 1 fpat 0 get length 1 sub {
        /x exch def
        /fpb fpat y get x get def
        pixs x y qmv fpb put
        format (full) eq {
            pixs size x sub 1 sub y qmv fpb put
            pixs x size y sub 1 sub qmv fpb put
        } if
      } for
    } for
    
    % Alignment patterns
    /algnpat [
        [ 1 1 1 1 1 ]
        [ 1 0 0 0 1 ]
        [ 1 0 1 0 1 ]
        [ 1 0 0 0 1 ]
        [ 1 1 1 1 1 ]
    ] def
    /putalgnpat {
        /py exch def
        /px exch def
        0 1 4 {
            /pb exch def
            0 1 4 {
                /pa exch def
                pixs px pa add py pb add qmv algnpat pb get pa get put
            } for
        } for
    } bind def
    asp2 2 sub asp3 asp2 sub size 13 sub {
        /i exch def
        i 4 putalgnpat
        4 i putalgnpat
    } for
    asp2 2 sub asp3 asp2 sub size 9 sub { 
        /x exch def
        asp2 2 sub asp3 asp2 sub size 9 sub {
            /y exch def
            x y putalgnpat
        } for
    } for
    
    % Timing patterns
    format (full) eq {
        8 1 size 9 sub {
            /i exch def
            pixs i 6 qmv i 1 add 2 mod put
            pixs 6 i qmv i 1 add 2 mod put
        } for
    } {
        8 1 size 1 sub {
            /i exch def
            pixs i 0 qmv i 1 add 2 mod put
            pixs 0 i qmv i 1 add 2 mod put
        } for
    } ifelse
    
    % Format information modules
    format (full) eq {
        /formatmap [
            [ [ 0 8 ] [ 8 size 1 sub ] ]  [ [ 1 8 ] [ 8 size 2 sub ] ]  [ [ 2 8 ] [ 8 size 3 sub ] ]
            [ [ 3 8 ] [ 8 size 4 sub ] ]  [ [ 4 8 ] [ 8 size 5 sub ] ]  [ [ 5 8 ] [ 8 size 6 sub ] ]
            [ [ 7 8 ] [ 8 size 7 sub ] ]  [ [ 8 8 ] [ size 8 sub 8 ] ]  [ [ 8 7 ] [ size 7 sub 8 ] ]
            [ [ 8 5 ] [ size 6 sub 8 ] ]  [ [ 8 4 ] [ size 5 sub 8 ] ]  [ [ 8 3 ] [ size 4 sub 8 ] ]
            [ [ 8 2 ] [ size 3 sub 8 ] ]  [ [ 8 1 ] [ size 2 sub 8 ] ]  [ [ 8 0 ] [ size 1 sub 8 ] ]
        ] def
    } {
        /formatmap [
            [ [ 1 8 ] ]  [ [ 2 8 ] ]  [ [ 3 8 ] ]  [ [ 4 8 ] ]  [ [ 5 8 ] ]
            [ [ 6 8 ] ]  [ [ 7 8 ] ]  [ [ 8 8 ] ]  [ [ 8 7 ] ]  [ [ 8 6 ] ]
            [ [ 8 5 ] ]  [ [ 8 4 ] ]  [ [ 8 3 ] ]  [ [ 8 2 ] ]  [ [ 8 1 ] ]
        ] def
    } ifelse
    formatmap {
        { {} forall qmv pixs exch 0 put } forall
    } forall
    
    % Version information modules
    size 45 ge {
        /versionmap [
            [ [ size  9 sub 5 ] [ 5 size  9 sub ] ]  [ [ size 10 sub 5 ] [ 5 size 10 sub ] ]
            [ [ size 11 sub 5 ] [ 5 size 11 sub ] ]  [ [ size  9 sub 4 ] [ 4 size  9 sub ] ]
            [ [ size 10 sub 4 ] [ 4 size 10 sub ] ]  [ [ size 11 sub 4 ] [ 4 size 11 sub ] ]
            [ [ size  9 sub 3 ] [ 3 size  9 sub ] ]  [ [ size 10 sub 3 ] [ 3 size 10 sub ] ]
            [ [ size 11 sub 3 ] [ 3 size 11 sub ] ]  [ [ size  9 sub 2 ] [ 2 size  9 sub ] ]
            [ [ size 10 sub 2 ] [ 2 size 10 sub ] ]  [ [ size 11 sub 2 ] [ 2 size 11 sub ] ]
            [ [ size  9 sub 1 ] [ 1 size  9 sub ] ]  [ [ size 10 sub 1 ] [ 1 size 10 sub ] ]
            [ [ size 11 sub 1 ] [ 1 size 11 sub ] ]  [ [ size  9 sub 0 ] [ 0 size  9 sub ] ]
            [ [ size 10 sub 0 ] [ 0 size 10 sub ] ]  [ [ size 11 sub 0 ] [ 0 size 11 sub ] ]
        ] def
    } {
        /versionmap [] def
    } ifelse
    versionmap {
        { {} forall qmv pixs exch 0 put } forall
    } forall
    
    % Solitary dark module in full symbols
    format (full) eq {
        pixs 8 size 8 sub qmv 1 put
    } if
    
    % Calculate the mask patterns
    format (full) eq {
        /maskfuncs [ 
            {add 2 mod} bind
            {exch pop 2 mod} bind
            {pop 3 mod} bind
            {add 3 mod} bind
            {2 idiv exch 3 idiv add 2 mod} bind
            {mul dup 2 mod exch 3 mod add} bind
            {mul dup 2 mod exch 3 mod add 2 mod} bind
            {2 copy mul 3 mod 3 1 roll add 2 mod add 2 mod} bind
        ] def
    } {
        /maskfuncs [ 
            {exch pop 2 mod} bind
            {2 idiv exch 3 idiv add 2 mod} bind
            {mul dup 2 mod exch 3 mod add 2 mod} bind
            {2 copy mul 3 mod 3 1 roll add 2 mod add 2 mod} bind
        ] def
    } ifelse
    /masks maskfuncs length array def
    0 1 masks length 1 sub {
        /m exch def
        /mask size size mul array def
        0 1 size 1 sub {
            /j exch def
            0 1 size 1 sub {
                /i exch def
                i j maskfuncs m get exec 0 eq 
                pixs i j qmv get -1 eq and {1} {0} ifelse
                mask i j qmv 3 -1 roll put
            } for
        } for
        masks m mask put
    } for
    
    % Walk the symbol placing the bitstream
    /posx size 1 sub def
    /posy size 1 sub def
    /dir -1 def  % -1 is upwards, 1 is downwards
    /col 1 def   % 0 is left bit, 1 is right bit
    /num 0 def
    { % loop
        posx 0 lt {exit} if
        pixs posx posy qmv get -1 eq {
            cws num 8 idiv get 7 num 8 mod sub neg bitshift 1 and
            pixs posx posy qmv 3 -1 roll put
            /num num 1 add def
        } if
        col 1 eq {
            /col 0 def
            /posx posx 1 sub def
        } {
            /col 1 def
            /posx posx 1 add def 
            /posy posy dir add def
            posy 0 lt posy size ge or {  % Turn around at top and bottom
                /dir dir -1 mul def
                /posy posy dir add def
                /posx posx 2 sub def
                % Hop over the timing pattern in full size symbols
                format (full) eq posx 6 eq and {/posx posx 1 sub def} if
            } if
        } ifelse
    } loop
    
    % Evaluation algorithm for full symbols
    /evalfull {
        /sym exch def
        m 2 eq {1} {2} ifelse  % In future we may evaluate the masks
    } bind def
    
    % Evaluation algoritm for micro symbols
    /evalmicro {
        /sym exch def
        /dkrhs 0 def /dkbot 0 def
        1 1 size 1 sub {
            /i exch def
            /dkrhs dkrhs sym size 1 sub i qmv get add def
            /dkbot dkbot sym i size 1 sub qmv get add def
        } for
        dkrhs dkbot le {
            dkrhs 16 mul dkbot add neg
        } {
            dkbot 16 mul dkrhs add neg
        } ifelse
    } bind def
    
    % Evaluate the masked symbols to find the most suitable
    /bestscore 999999999 def
    0 1 masks length 1 sub {
        /m exch def
        /masksym size size mul array def
        0 1 size size mul 1 sub {
            /i exch def
            masksym i pixs i get masks m get i get xor put
        } for
        format (full) eq {
            masksym evalfull /score exch def
        } {
            masksym evalmicro /score exch def
        } ifelse
        score bestscore lt { 
            /bestsym masksym def
            /bestmaskval m def
            /bestscore score def
        } if    
    } for
    /pixs bestsym def
    
    % Add the format information
    format (full) eq {
        /fmtvals [
            16#5412 16#5125 16#5e7c 16#5b4b 16#45f9 16#40ce 16#4f97 16#4aa0 
            16#77c4 16#72f3 16#7daa 16#789d 16#662f 16#6318 16#6c41 16#6976
            16#1689 16#13be 16#1ce7 16#19d0 16#0762 16#0255 16#0d0c 16#083b 
            16#355f 16#3068 16#3f31 16#3a06 16#24b4 16#2183 16#2eda 16#2bed
        ] def
        /ecid (MLHQ) eclevel search pop length exch pop exch pop def
        /fmtval fmtvals ecid 3 bitshift bestmaskval add get def
    } {
        /fmtvals [
            16#4445 16#4172 16#4e2b 16#4b1c 16#55ae 16#5099 16#5fc0 16#5af7
            16#6793 16#62a4 16#6dfd 16#68ca 16#7678 16#734f 16#7c16 16#7921
            16#06de 16#03e9 16#0cb0 16#0987 16#1735 16#1202 16#1d5b 16#186c
            16#2508 16#203f 16#2f66 16#2a51 16#34e3 16#31d4 16#3e8d 16#3bba
        ] def
        /symid [ [0] [1 2] [3 4] [5 6 7] ] size 11 sub 2 idiv get eclval get def
        /fmtval fmtvals symid 2 bitshift bestmaskval add get def
    } ifelse
    0 1 formatmap length 1 sub {
        /i exch def
        formatmap i get {
            pixs exch {} forall qmv fmtval 14 i sub neg bitshift 1 and put
        } forall
    } for
    
    % Add the version information
    size 45 ge {
        /vervals [
            16#07c94 16#085bc 16#09a99 16#0a4d3 16#0bbf6 16#0c762 16#0d847 
            16#0e60d 16#0f928 16#10b78 16#1145d 16#12a17 16#13532 16#149a6 
            16#15683 16#168c9 16#177ec 16#18ec4 16#191e1 16#1afab 16#1b08e 
            16#1cc1a 16#1d33f 16#1ed75 16#1f250 16#209d5 16#216fd 16#228ba 
            16#2379f 16#24b0b 16#2542e 16#26a64 16#27541 16#28c69
        ] def
        /verval vervals size 17 sub 4 idiv 7 sub get def
        0 1 versionmap length 1 sub {
            /i exch def
            versionmap i get {
                pixs exch {} forall qmv verval 17 i sub neg bitshift 1 and put
            } forall
        } for
    } if
    
    /retval 7 dict def
    retval (ren) (renmatrix) put
    retval (pixs) pixs put
    retval (pixx) size put
    retval (pixy) size put
    retval (height) size 2 mul 72 div put
    retval (width) size 2 mul 72 div put
    retval (opt) useropts put
    retval

    end

} bind def
/qrcode load 0 1 dict put
% --END ENCODER qrcode--

% --BEGIN ENCODER maxicode--
% --DESC: MaxiCode
% --EXAM: ^059^042^041^059^040^03001^02996152382802^029840^029001^0291Z00004951^029UPSN^02906X610^029159^0291234567^0291^0471^029^029Y^029634 ALPHA DR^029PITTSBURGH^029PA^030^062^004^063
% --EXOP: mode=2
% --RNDR: renmaximatrix
/maxicode {

    0 begin

    /options exch def        % We are given an option string
    /useropts options def
    /barcode exch def        % We are given a barcode string

    /mode 4 def
    /sam -1 def

    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop

    /mode mode cvi def
    /sam sam cvi def

    /txtvals (@ABCDEFGHIJKLMNOPQRSTUVWXYZ@@@@@ @@@@@@@@@@@@@@@0123456789@@@@@@) def

    % Parse a given message into codewords
    /maxiparse {
        /txt exch def
        /out txt length array def
        /i 0 def /j 0 def
        { % loop  
            i txt length eq {exit} if
            txt i 1 getinterval (^) eq {
                % Codeword is given by the next three characters
                /cw txt i 1 add 3 getinterval cvi def
                /i i 4 add def
            } {
                % Codeword is the characters position in txtvals
                txtvals txt i 1 getinterval search 
                pop length /cw exch def pop pop
                /i i 1 add def
            } ifelse
            out j cw put
            /j j 1 add def 
        } loop
        out 0 j getinterval
    } bind def

    % Calcalate the structured append mode insert
    /sami () def
    sam -1 ne {
        /sami (^033^000) 8 string copy def
        sam 10 idiv 1 sub 8 mul sam 10 mod 1 sub add 10 2 string cvrs
        dup length 8 exch sub sami exch 3 -1 roll putinterval 
    } if

    % Message handling for modes 2 and 3
    mode 2 eq mode 3 eq or {

        /msg barcode def

        % Normalise messages that begin with a field identifier [)>RS01GSyy
        msg (^059^042^041^059^040^03001^029) search {
            pop
            dup length 2 add string /fid exch def
            fid 0 3 -1 roll putinterval
            dup fid fid length 2 sub 3 -1 roll 0 2 getinterval putinterval
            dup length 2 sub 2 exch getinterval /msg exch def
        } {
            pop
            /fid () def
        } ifelse

        % Read the postcode, country code and service code fields
        msg (^029) search pop /pc exch def
        pop (^029) search pop /cc exch def
        pop (^029) search pop /sc exch def
        pop /msg exch def

        % Calculate the fixed-width binary values for the mode, postcode, country code and service
        /mdb (0000) 4 string copy dup mode cvi 2 4 string cvrs dup length 4 exch sub exch putinterval def
        /ccb (0000000000) 10 string copy dup cc cvi 2 10 string cvrs dup length 10 exch sub exch putinterval def
        /scb (0000000000) 10 string copy dup sc cvi 2 10 string cvrs dup length 10 exch sub exch putinterval def
        /pcb (000000000000000000000000000000000000) 36 string copy def
        mode 2 eq {
            % For numeric postcode, first six bits represent length and remaining 30 bits the value
            pcb pc length 2 6 string cvrs dup length 6 exch sub exch putinterval
            pcb pc cvi 2 30 string cvrs dup length 36 exch sub exch putinterval
        } {  % mode=3
            % For alphanumeric postcode, trim or pad with spaces to 6 chars and encode to binary
            /pccw (      ) 6 string copy dup 0 pc length 6 gt {pc 0 6 getinterval} {pc} ifelse putinterval maxiparse def
            0 1 5 {
                /i exch def
                pcb pccw i get 2 6 string cvrs dup length 6 i mul 6 add exch sub exch putinterval
            } for
        } ifelse

        % Convolute the binary values into the structured carrier message
        /scm 60 string def
        scm 2  mdb putinterval
        scm 38 pcb 0  4 getinterval putinterval
        scm 30 pcb 4  6 getinterval putinterval
        scm 24 pcb 10 6 getinterval putinterval
        scm 18 pcb 16 6 getinterval putinterval
        scm 12 pcb 22 6 getinterval putinterval
        scm 6  pcb 28 6 getinterval putinterval
        scm 0  pcb 34 2 getinterval putinterval
        scm 52 ccb 0  2 getinterval putinterval
        scm 42 ccb 2  6 getinterval putinterval
        scm 36 ccb 8  2 getinterval putinterval
        scm 54 scb 0  6 getinterval putinterval
        scm 48 scb 6  4 getinterval putinterval

        % Evaluate the structured carrier message as codewords
        /pri [ 0 0 0 0 0 0 0 0 0 0 ] def
        0 1 59 { 
            /i exch def
            /ps i 6 idiv def
            /ep 2 5 i 6 mod sub exp cvi scm i get 48 sub mul def
            pri ps pri ps get ep add put
        } for

        % Encode the secondary parts, including any SAM insert and field identifier
        /sec [ 84 {33} repeat ] def
        sec 0 [ sami maxiparse {} forall fid maxiparse {} forall msg maxiparse {} forall ] putinterval

    } if

    % Message handling for modes 4, 5 and 6
    mode 4 eq mode 5 eq or mode 6 eq or {

        % Prefix the message with the structured append insert
        /msg sami length barcode length add string def
        msg 0 sami putinterval
        msg sami length barcode putinterval

        % First symbol is the mode and the remainder are the padded message
        /cws [ mode 5 eq {78} {94} ifelse {33} repeat ] def
        cws 0 mode put
        cws 1 msg maxiparse putinterval

        % Fit the message into the primary and secondary components
        /pri cws 0 10 getinterval def
        /sec cws 10 cws length 10 sub getinterval def

    } if

    % Create the 64x64 Reed-Solomon table
    /rstable 64 64 mul array def
    rstable 0 [ 64 {0} repeat ] putinterval
    rstable 64 [ 0 1 63 {} for ] putinterval
    /prev 1 def
    64 {       
        /next prev 1 bitshift def
        next 64 and 0 ne {
            /next next 67 xor def
        } if        
        0 1 63 {
            /j exch def
            /nextcell {rstable 64 next mul j add} def
            nextcell rstable 64 prev mul j add get 1 bitshift put
            nextcell get 64 and 0 ne {
                nextcell nextcell get 67 xor put
            } if
        } for
        /prev next def
    } repeat

    % Calculate the parity codewords for primary codewords 
    /pgen [46 44 49 3 2 57 42 39 28 31 1] def
    /rscodes [ 10 {0} repeat 9 -1 0 { pri exch get } for ] def
    rscodes length 11 sub -1 0 {
        /i exch def
        0 1 10 {
            /j exch def
            rscodes i j add rscodes i j add get
            rstable 64 pgen j get mul rscodes i 10 add get add get
            xor put
        } for
    } for
    /prichk [ 9 -1 0 { rscodes exch get } for ] def

    % Split secondary codeword into odd and even elements
    /seco [ 0 2 sec length 1 sub { sec exch get } for ] def
    /sece [ 1 2 sec length 1 sub { sec exch get } for ] def

    % Calculate the parity codewords for secondary codeword parts based on mode
    sec length 84 eq {  % SEC mode
        /sgen [ 59 23 19 31 33 38 17 22 48 15 36 57 37 22 8 27 33 11 44 23 1 ] def
    } {  % EEC mode
        /sgen [ 28 11 20 7 43 9 41 34 49 46 37 40 55 34 45 61 13 23 29 22 10 35 55 41 10 53 45 22 1 ] def
    } ifelse
    /scodes sgen length 1 sub def
    /rscodes [ scodes {0} repeat seco length 1 sub -1 0 { seco exch get } for ] def
    rscodes length scodes sub 1 sub -1 0 {
        /i exch def
        0 1 scodes {
            /j exch def
            rscodes i j add rscodes i j add get
            rstable 64 sgen j get mul rscodes i scodes add get add get
            xor put
        } for
    } for
    /secochk [ scodes 1 sub -1 0 { rscodes exch get } for ] def
    /rscodes [ scodes {0} repeat sece length 1 sub -1 0 { sece exch get } for ] def
    rscodes length scodes sub 1 sub -1 0 {
        /i exch def
        0 1 scodes {
            /j exch def
            rscodes i j add rscodes i j add get
            rstable 64 sgen j get mul rscodes i scodes add get add get
            xor put
        } for
    } for
    /secechk [ scodes 1 sub -1 0 { rscodes exch get } for ] def

    % Recompose the secondary parity codewords
    /secchk [ 0 1 scodes 1 sub { dup secochk exch get exch secechk exch get } for ] def

    % Concatinate the data into final codewords
    /codewords [
        pri {} forall 
        prichk {} forall
        sec {} forall 
        secchk {} forall
    ] def

    % Convert the codewords into module bits
    /mods [ 864 {0} repeat ] def
    0 1 143 {
        /i exch def
        /cw [ codewords i get 2 6 string cvrs {48 sub} forall ] def
        mods 6 i mul 6 cw length sub add cw putinterval
    } for

    % Maps modules to pixels in the grid
    /modmap [
        469 529 286 316 347 346 673 672 703 702 647 676 283 282 313 312 370 610 618 379 
        378 409 408 439 705 704 559 589 588 619 458 518 640 701 675 674 285 284 315 314 
        310 340 531 289 288 319 349 348 456 486 517 516 471 470 369 368 399 398 429 428 
        549 548 579 578 609 608 649 648 679 678 709 708 639 638 669 668 699 698 279 278 
        309 308 339 338 381 380 411 410 441 440 561 560 591 590 621 620 547 546 577 576 
        607 606 367 366 397 396 427 426 291 290 321 320 351 350 651 650 681 680 711 710 
        1   0   31  30  61  60  3   2   33  32  63  62  5   4   35  34  65  64  7   6   
        37  36  67  66  9   8   39  38  69  68  11  10  41  40  71  70  13  12  43  42  
        73  72  15  14  45  44  75  74  17  16  47  46  77  76  19  18  49  48  79  78  
        21  20  51  50  81  80  23  22  53  52  83  82  25  24  55  54  85  84  27  26  
        57  56  87  86  117 116 147 146 177 176 115 114 145 144 175 174 113 112 143 142 
        173 172 111 110 141 140 171 170 109 108 139 138 169 168 107 106 137 136 167 166 
        105 104 135 134 165 164 103 102 133 132 163 162 101 100 131 130 161 160 99  98  
        129 128 159 158 97  96  127 126 157 156 95  94  125 124 155 154 93  92  123 122 
        153 152 91  90  121 120 151 150 181 180 211 210 241 240 183 182 213 212 243 242 
        185 184 215 214 245 244 187 186 217 216 247 246 189 188 219 218 249 248 191 190 
        221 220 251 250 193 192 223 222 253 252 195 194 225 224 255 254 197 196 227 226 
        257 256 199 198 229 228 259 258 201 200 231 230 261 260 203 202 233 232 263 262 
        205 204 235 234 265 264 207 206 237 236 267 266 297 296 327 326 357 356 295 294 
        325 324 355 354 293 292 323 322 353 352 277 276 307 306 337 336 275 274 305 304 
        335 334 273 272 303 302 333 332 271 270 301 300 331 330 361 360 391 390 421 420 
        363 362 393 392 423 422 365 364 395 394 425 424 383 382 413 412 443 442 385 384 
        415 414 445 444 387 386 417 416 447 446 477 476 507 506 537 536 475 474 505 504 
        535 534 473 472 503 502 533 532 455 454 485 484 515 514 453 452 483 482 513 512 
        451 450 481 480 511 510 541 540 571 570 601 600 543 542 573 572 603 602 545 544 
        575 574 605 604 563 562 593 592 623 622 565 564 595 594 625 624 567 566 597 596 
        627 626 657 656 687 686 717 716 655 654 685 684 715 714 653 652 683 682 713 712 
        637 636 667 666 697 696 635 634 665 664 695 694 633 632 663 662 693 692 631 630 
        661 660 691 690 721 720 751 750 781 780 723 722 753 752 783 782 725 724 755 754 
        785 784 727 726 757 756 787 786 729 728 759 758 789 788 731 730 761 760 791 790 
        733 732 763 762 793 792 735 734 765 764 795 794 737 736 767 766 797 796 739 738 
        769 768 799 798 741 740 771 770 801 800 743 742 773 772 803 802 745 744 775 774 
        805 804 747 746 777 776 807 806 837 836 867 866 897 896 835 834 865 864 895 894 
        833 832 863 862 893 892 831 830 861 860 891 890 829 828 859 858 889 888 827 826 
        857 856 887 886 825 824 855 854 885 884 823 822 853 852 883 882 821 820 851 850 
        881 880 819 818 849 848 879 878 817 816 847 846 877 876 815 814 845 844 875 874 
        813 812 843 842 873 872 811 810 841 840 871 870 901 900 931 930 961 960 903 902 
        933 932 963 962 905 904 935 934 965 964 907 906 937 936 967 966 909 908 939 938 
        969 968 911 910 941 940 971 970 913 912 943 942 973 972 915 914 945 944 975 974 
        917 916 947 946 977 976 919 918 949 948 979 978 921 920 951 950 981 980 923 922 
        953 952 983 982 925 924 955 954 985 984 927 926 957 956 987 986 58  89  88  118 
        149 148 178 209 208 238 269 268 298 329 328 358 389 388 418 449 448 478 509 508 
        538 569 568 598 629 628 658 689 688 718 749 748 778 809 808 838 869 868 898 929 
        928 958 989 988
    ] def

    % Lookup pixels for enabled modules from modmap
    /pixs 864 array def
    /j 0 def
    0 1 mods length 1 sub {
        /i exch def
        mods i get 1 eq {
            pixs j modmap i get put
            /j j 1 add def
        } if
    } for
    /pixs [ pixs 0 j getinterval {} forall 28 29 280 281 311 457 488 500 530 670 700 677 707 ] def

    /retval 3 dict def
    retval (ren) (renmaximatrix) put
    retval (pixs) pixs put
    retval (opt) useropts put
    retval

    end

} bind def
/maxicode load 0 1 dict put
% --END ENCODER maxicode--

% --BEGIN ENCODER azteccode--
% --DESC: Aztec Code
% --EXAM: 00100111001000000101001101111000010100111100101000000110
% --EXOP: format=compact
% --RNDR: renmatrix
/azteccode {

    0 begin

    /options exch def
    /useropts options def
    /barcode exch def

    /format (unset) def    % full, compact or rune
    /readerinit false def
    /layers -1 def
    /eclevel 23 def
    /ecaddchars 3 def

    % Parse the input options
    options {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
    
    /layers layers cvi def
    /eclevel eclevel cvr def
    /ecaddchars ecaddchars cvi def
    
    % Convert from input into message bitstream
    /msgbits () def 
    format (rune) ne {/msgbits barcode def} if 
   
    % Lookup the most appropriate symbol specification 
    /metrics [
        [ (rune)     0 0    0  6 ]  % Special metric for rune symbols
        [ (compact)  1 1   17  6 ] [ (full)     1 1   21  6 ] [ (compact)  2 0   40  6 ]
        [ (full)     2 1   48  6 ] [ (compact)  3 0   51  8 ] [ (full)     3 1   60  8 ]
        [ (compact)  4 0   76  8 ] [ (full)     4 1   88  8 ] [ (full)     5 1  120  8 ]
        [ (full)     6 1  156  8 ] [ (full)     7 1  196  8 ] [ (full)     8 1  240  8 ]
        [ (full)     9 1  230 10 ] [ (full)    10 1  272 10 ] [ (full)    11 1  316 10 ]
        [ (full)    12 1  364 10 ] [ (full)    13 1  416 10 ] [ (full)    14 1  470 10 ]
        [ (full)    15 1  528 10 ] [ (full)    16 1  588 10 ] [ (full)    17 1  652 10 ]
        [ (full)    18 1  720 10 ] [ (full)    19 1  790 10 ] [ (full)    20 1  864 10 ]
        [ (full)    21 1  940 10 ] [ (full)    22 1 1020 10 ] [ (full)    23 0  920 12 ]
        [ (full)    24 0  992 12 ] [ (full)    25 0 1066 12 ] [ (full)    26 0 1144 12 ]
        [ (full)    27 0 1224 12 ] [ (full)    28 0 1306 12 ] [ (full)    29 0 1392 12 ]
        [ (full)    30 0 1480 12 ] [ (full)    31 0 1570 12 ] [ (full)    32 0 1664 12 ]
    ] def

    /i 0 def
    { % loop
        /m metrics i get def
        /frmt m 0 get def                          % Format of the symbol
        /mlyr m 1 get def                          % Data layers
        /icap m 2 get def                          % Reader initialisation capable
        /ncws m 3 get def                          % Total of codewords
        /bpcw m 4 get def                          % Bits per codeword
        /numecw ncws eclevel mul 100 div ecaddchars add ceiling cvi def
        msgbits length 0 eq {/numecw 0 def} if     % Error correction codewords 
        /numdcw ncws numecw sub def                % Data codewords
        /okay true def
        format (unset) ne format frmt ne and {/okay false def} if
        readerinit icap 1 ne and {/okay false def} if
        layers -1 ne layers mlyr ne and {/okay false def} if 
        msgbits length bpcw div ceiling cvi numdcw gt {/okay false def} if
        okay {exit} if
        /i i 1 add def
    } loop
    /layers mlyr def
    /format frmt def

    % Expand message bits into codewords avoiding codewords with all zeros or all ones
    /allzero {dup length (000000000000) 0 3 -1 roll getinterval eq} bind def
    /allones {dup length (111111111111) 0 3 -1 roll getinterval eq} bind def
    /cws ncws array def
    /m 0 def /c 0 def
    {
        msgbits length m le {exit} if
        msgbits length m sub bpcw ge {
            /cwb msgbits m bpcw 1 sub getinterval def        % All but last bit
            /cwf msgbits m bpcw add 1 sub 1 getinterval def  % Last bit
            cwb allzero {/cwf (1) def /m m 1 sub def} if     % Flip last bit to avoid zeros
            cwb allones {/cwf (0) def /m m 1 sub def} if     % Flip last bit to avoid ones
            % Concatinate the bits 
            12 string dup 0 cwb putinterval 
            dup bpcw 1 sub cwf putinterval
            0 bpcw getinterval
            /cwb exch def
        } {  %  Final codeword
            /cwb msgbits m msgbits length m sub getinterval def
            /cwb (111111111111) 12 string copy dup 0 cwb putinterval 0 bpcw getinterval def
            cwb allones {cwb cwb length 1 sub (0) putinterval} if  % Prevent all ones
        } ifelse
        % Conversion of binary data into byte array
        /cw 0 def
        0 1 bpcw 1 sub {
            /i exch def
            /cw cw 2 bpcw i sub 1 sub exp cvi cwb i get 48 sub mul add def
        } for
        cws c cw put
        /m m bpcw add def 
        /c c 1 add def
    } loop    
    /cws cws 0 c getinterval def

    % Reed-Solomon algorithm
    /rscodes {

        /rspm exch def
        /rsgf exch def
        /rsnc exch def
        /rscws exch def

        % Calculate the log and anti-log tables
        /rslog [ 1 rsgf sub rsgf 1 sub {0} repeat ] def
        /rsalog [ 1 rsgf 1 sub {0} repeat ] def
        1 1 rsgf 1 sub {
            /i exch def
            rsalog i rsalog i 1 sub get 2 mul put
            rsalog i get rsgf ge { rsalog i rsalog i get rspm xor put } if
            rslog rsalog i get i put
        } for

        % Function to calculate the product in the field
        /rsprod {
            /y exch def
            /x exch def
            x y mul 0 ne { 
                rsalog rslog x get rslog y get add rsgf 1 sub mod get
            } {
                0
            } ifelse
        } bind def

        % Generate the coefficients
        /coeffs [ 1 rsnc {0} repeat ] def
        1 1 rsnc {
            /i exch def 
            coeffs i coeffs i 1 sub get put
            i 1 sub -1 1 {
                /j exch def
                coeffs j coeffs j 1 sub get coeffs j get rsalog i get rsprod xor put
            } for 
            coeffs 0 coeffs 0 get rsalog i get rsprod put
        } for

        % Extend the input with the error correction values
        /nd rscws length def
        /rscws [ rscws {} forall rsnc {0} repeat 0 ] def
        0 1 nd 1 sub {
            /k exch rscws exch get rscws nd get xor def 
            0 1 rsnc 1 sub {
                /j exch def 
                rscws nd j add rscws nd j add 1 add get k coeffs rsnc j sub 1 sub get rsprod xor put
            } for 
        } for

        % Return all but the last codeword
        rscws 0 rscws length 1 sub getinterval

    } bind def

    % Create the codewords and bit string for the mode
    format (full) eq {
        /mode layers 1 sub 11 bitshift cws length 1 sub add def
        readerinit {/mode mode 2#1000000000000000 or def} if
        /mode [
            mode 2#1111000000000000 and -12 bitshift
            mode 2#0000111100000000 and -8 bitshift
            mode 2#0000000011110000 and -4 bitshift
            mode 2#0000000000001111 and
        ] def
        /mode mode 6 16 19 rscodes def 
    } if
    format (compact) eq {
        /mode layers 1 sub 6 bitshift cws length 1 sub add def
        readerinit {/mode mode 2#10000000 or def} if 
        /mode [
            mode 2#11110000 and -4 bitshift
            mode 2#00001111 and
        ] def
        /mode mode 5 16 19 rscodes def
    } if
    format (rune) eq {
        /mode barcode cvi def
        /mode [
            mode 2#11110000 and -4 bitshift
            mode 2#00001111 and
        ] def
        /mode mode 5 16 19 rscodes def
        /mode [mode {2#1010 xor} forall] def  % Invert alternate bits
    } if
    /modebits mode length 4 mul string def
    0 1 modebits length 1 sub {modebits exch (0) putinterval} for
    0 1 mode length 1 sub {
        /i exch def
        modebits mode i get 2 4 string cvrs dup length 4 exch sub 4 i mul add exch putinterval 
    } for

    % Extend the data codewords with error correction codewords to create the bit string for the data
    /rsparams [
        [] [] [] [] [] [] 
        [ 64 67 ]      % 6-bit codewords 
        []
        [ 256 301 ]    % 8-bit codewords
        [] 
        [ 1024 1033 ]  % 10-bit codewords
        []
        [ 4096 4201 ]  % 12-bit codewords
    ] def
    /cws cws ncws cws length sub rsparams bpcw get {} forall rscodes def
    format (full) eq {
        /databits layers layers mul 16 mul layers 112 mul add string def 
    } {
        /databits layers layers mul 16 mul layers 88 mul add string def 
    } ifelse
    0 1 databits length 1 sub {databits exch (0) putinterval} for
    0 1 ncws 1 sub { 
        /i exch def
        databits cws i get 2 bpcw string cvrs 
        dup length bpcw exch sub bpcw i mul add databits length ncws bpcw mul sub add 
        exch putinterval 
    } for

    % Move to a point in the cartesian plane centered on the bullseye
    /cmv {size mul sub mid add} bind def

    % Move to a bit position within a layer
    /lmv {
        /lbit exch def
        /llyr exch def
        /lwid fw llyr 4 mul add def
        /ldir lbit 2 idiv lwid idiv def
        ldir 0 eq {  % Top
            lwid 1 sub 2 idiv neg 1 add lbit 2 idiv lwid mod add 
            fw 1 sub 2 idiv llyr 2 mul add lbit 2 mod add
            cmv
        } if
        ldir 1 eq {  % Right
            fw 2 idiv llyr 2 mul add lbit 2 mod add
            lwid 1 sub 2 idiv 1 sub lbit 2 idiv lwid mod sub
            cmv
        } if
        ldir 2 eq {  % Bottom
            lwid 2 idiv neg 1 add lbit 2 idiv lwid mod add neg
            fw 2 idiv llyr 2 mul add lbit 2 mod add neg
            cmv
        } if
        ldir 3 eq {  % Left
            fw 1 sub 2 idiv llyr 2 mul add lbit 2 mod add neg
            lwid 2 idiv 1 sub lbit 2 idiv lwid mod sub neg
            cmv
        } if
    } bind def

    % Create the pixel map
    % For full symbols we disregard the reference grid at this stage
    format (full) eq {/fw 12 def} {/fw 9 def} ifelse
    /size fw layers 4 mul add 2 add def 
    /pixs [size size mul {-1} repeat] def
    /mid size 1 sub 2 idiv size mul size 1 sub 2 idiv add def

    % Data layers
    /i 0 def
    1 1 layers {
        /layer exch def
        0 1 fw layer 4 mul add 8 mul 1 sub {
            /pos exch def
            pixs layer pos lmv databits databits length i sub 1 sub get 48 sub put
            /i i 1 add def
        } for
    } for

    % For full symbols expand the pixel map by inserting the reference grid
    format (full) eq {
        /fw 13 def
        /size fw layers 4 mul add 2 add layers 10.5 add 7.5 div 1 sub cvi 2 mul add def
        /mid size size mul 2 idiv def
        /npixs [size size mul {-2} repeat] def
        0 16 size 2 idiv {
            /i exch def
            0 1 size 1 sub {
                /j exch def
                npixs size 2 idiv neg j add i cmv     [size 2 idiv j add i add 1 add 2 mod] putinterval
                npixs size 2 idiv neg j add i neg cmv [size 2 idiv j add i add 1 add 2 mod] putinterval
                npixs i size 2 idiv neg j add cmv     [size 2 idiv j add i add 1 add 2 mod] putinterval
                npixs i neg size 2 idiv neg j add cmv [size 2 idiv j add i add 1 add 2 mod] putinterval
            } for
        } for 
        /j 0 def
        0 1 npixs length 1 sub {
            /i exch def
            npixs i get -2 eq {
                npixs i pixs j get put
                /j j 1 add def
            } if
        } for
        /pixs npixs def
    } if

    % Finder pattern
    /fw fw 2 idiv def
    fw neg 1 fw {
        /i exch def
        fw neg 1 fw {
            /j exch def
            pixs i j cmv
            i abs j abs gt {i abs} {j abs} ifelse 1 add 2 mod
            put
        } for
    } for

    % Orientation bits
    [ [ fw 1 add neg   fw             1 ] [ fw 1 add neg   fw 1 add       1 ]
      [ fw neg         fw 1 add       1 ] [ fw 1 add       fw 1 add       1 ]
      [ fw 1 add       fw             1 ] [ fw 1 add       fw neg         1 ]
      [ fw             fw 1 add       0 ] [ fw 1 add       fw 1 add neg   0 ]
      [ fw             fw 1 add neg   0 ] [ fw neg         fw 1 add neg   0 ]
      [ fw 1 add neg   fw 1 add neg   0 ] [ fw 1 add neg   fw neg         0 ]
    ] {pixs exch {} forall 3 1 roll cmv exch put} forall

    % Mode ring
    format (full) eq {
        /modemap [ 
            [-5  7] [-4  7] [-3  7] [-2  7] [-1  7] [ 1  7] [ 2  7] [ 3  7] [ 4  7] [ 5  7]
            [ 7  5] [ 7  4] [ 7  3] [ 7  2] [ 7  1] [ 7 -1] [ 7 -2] [ 7 -3] [ 7 -4] [ 7 -5]
            [ 5 -7] [ 4 -7] [ 3 -7] [ 2 -7] [ 1 -7] [-1 -7] [-2 -7] [-3 -7] [-4 -7] [-5 -7]
            [-7 -5] [-7 -4] [-7 -3] [-7 -2] [-7 -1] [-7  1] [-7  2] [-7  3] [-7  4] [-7  5]
        ] def
    } {
        /modemap [
            [-3  5] [-2  5] [-1  5] [ 0  5] [ 1  5] [ 2  5] [ 3  5]
            [ 5  3] [ 5  2] [ 5  1] [ 5  0] [ 5 -1] [ 5 -2] [ 5 -3]
            [ 3 -5] [ 2 -5] [ 1 -5] [ 0 -5] [-1 -5] [-2 -5] [-3 -5]
            [-5 -3] [-5 -2] [-5 -1] [-5  0] [-5  1] [-5  2] [-5  3]
        ] def
    } ifelse
    0 1 modemap length 1 sub {
        /i exch def
        pixs modemap i get {} forall cmv modebits i get 48 sub put
    } for

    /retval 7 dict def
    retval (ren) (renmatrix) put
    retval (pixs) pixs put
    retval (pixx) size put
    retval (pixy) size put
    retval (height) size 2 mul 72 div put
    retval (width) size 2 mul 72 div put
    retval (opt) useropts put
    retval

    end

} bind def
/azteccode load 0 1 dict put
% --END ENCODER azteccode--

% --BEGIN RENDERER renlinear--
/renlinear {

    0 begin          % Confine variables to local scope

    /args exch def   % We are given some arguments

    % Default options
    /sbs [] def
    /bhs [] def
    /bbs [] def
    /txt [] def
    /barcolor (unset) def
    /includetext false def
    /textcolor (unset) def
    /textxalign (unset) def
    /textyalign (unset) def
    /textfont (Courier) def
    /textsize 10 def
    /textxoffset 0 def
    /textyoffset 0 def
    /bordercolor (unset) def
    /backgroundcolor (unset) def
    /inkspread 0.15 def
    /width 0 def
    /barratio 1 def
    /spaceratio 1 def
    /showborder false def
    /borderleft 10 def
    /borderright 10 def
    /bordertop 1 def
    /borderbottom 1 def
    /borderwidth 0.5 def
    /guardwhitespace false def
    /guardleftpos 0 def
    /guardleftypos 0 def
    /guardrightpos 0 def
    /guardrightypos 0 def
    /guardwidth 6 def
    /guardheight 7 def
    
    % Apply the renderer options
    args {exch cvlit exch def} forall
 
    % Parse the user options   
    opt {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop

    /barcolor barcolor cvlit def
    /textcolor textcolor cvlit def
    /textxalign textxalign cvlit def
    /textyalign textyalign cvlit def
    /textfont textfont cvlit def
    /textsize textsize cvr def
    /textxoffset textxoffset cvr def
    /textyoffset textyoffset cvr def
    /bordercolor bordercolor cvlit def
    /backgroundcolor backgroundcolor cvlit def
    /inkspread inkspread cvr def
    /width width cvr def
    /barratio barratio cvr def
    /spaceratio spaceratio cvr def
    /borderleft borderleft cvr def
    /borderright borderright cvr def
    /bordertop bordertop cvr def
    /borderbottom borderbottom cvr def
    /borderwidth borderwidth cvr def
    /guardleftpos guardleftpos cvr def
    /guardleftypos guardleftypos cvr def
    /guardrightpos guardrightpos cvr def
    /guardrightypos guardrightypos cvr def
    /guardwidth guardwidth cvr def
    /guardheight guardheight cvr def
    
    % Create bar elements and put them into the bars array
    /bars sbs length 1 add 2 idiv array def
    /x 0.00 def /maxh 0 def
    0 1 sbs length 1 add 2 idiv 2 mul 2 sub {
        /i exch def
        i 2 mod 0 eq {           % i is even
            /d sbs i get barratio mul barratio sub 1 add def  % d=digit*r-r+1 
            /h bhs i 2 idiv get 72 mul def  % Height from bhs
            /c d 2 div x add def            % Centre of the bar = x + d/2
            /y bbs i 2 idiv get 72 mul def  % Baseline from bbs
            /w d inkspread sub def          % bar width = digit - inkspread
            bars i 2 idiv [h c y w] put     % Add the bar entry
            h maxh gt {/maxh h def} if
        } {
            /d sbs i get spaceratio mul spaceratio sub 1 add def  % d=digit*r-r+1 
        } ifelse
        /x x d add def  % x+=d
    } for

    gsave

    currentpoint translate

    % Force symbol to given width
    width 0 ne {
        width 72 mul x div 1 scale
    } if

    % Set RGB or CMYK color depending on length of given hex string
    /setanycolor {
        /anycolor exch def
        anycolor length 6 eq {
            (<      >) 8 string copy dup 1 anycolor putinterval cvx exec {255 div} forall setrgbcolor
        } if
        anycolor length 8 eq {
            (<        >) 10 string copy dup 1 anycolor putinterval cvx exec {255 div} forall setcmykcolor
        } if
    } bind def

    % Display the border and background
    newpath
    borderleft neg borderbottom neg moveto
    x borderleft add borderright add 0 rlineto
    0 maxh borderbottom add bordertop add rlineto
    x borderleft add borderright add neg 0 rlineto
    0 maxh borderbottom add bordertop add neg rlineto    
    closepath
    backgroundcolor (unset) ne { gsave backgroundcolor setanycolor fill grestore } if     
    showborder {
        gsave
        bordercolor (unset) ne { bordercolor setanycolor } if
        borderwidth setlinewidth stroke
        grestore
    } if    
   
    % Display the bars for elements in the bars array
    gsave
    barcolor (unset) ne { barcolor setanycolor } if
    bars {
        {} forall
        newpath setlinewidth moveto 0 exch rlineto stroke
    } forall
    grestore
    
    % Display the text for elements in the text array
    textcolor (unset) ne { textcolor setanycolor } if
    includetext {
    textxalign (unset) eq textyalign (unset) eq and {
        /s 0 def /f () def
        txt {
            {} forall
            2 copy s ne exch f ne or {
                2 copy /s exch def /f exch def            
                exch findfont exch scalefont setfont          
            } {
                pop pop
            } ifelse
            moveto show
        } forall
    } {
        textfont findfont textsize scalefont setfont
        /txt [ txt { 0 get {} forall } forall ] def
        /tstr txt length string def
        0 1 txt length 1 sub { dup txt exch get tstr 3 1 roll put } for
        /textxpos textxoffset x tstr stringwidth pop sub 2 div add def
        textxalign (left) eq { /textxpos textxoffset def } if
        textxalign (right) eq { /textxpos x textxoffset sub tstr stringwidth pop sub def } if
        textxalign (offleft) eq { /textxpos tstr stringwidth pop textxoffset add neg def } if
        textxalign (offright) eq { /textxpos x textxoffset add def } if
        /textypos textyoffset textsize add 3 sub neg def
        textyalign (above) eq { /textypos textyoffset maxh add 1 add def } if
        textyalign (center) eq { /textypos textyoffset maxh textsize 4 sub sub 2 div add def } if
        textxpos textypos moveto tstr show
    } ifelse
    } if    

    % Display the guard elements
    guardwhitespace {
        0.75 setlinewidth
        guardleftpos 0 ne {
            newpath
            guardleftpos neg guardwidth add guardleftypos guardwidth 2 div add moveto
            guardwidth neg guardheight -2 div rlineto
            guardwidth guardheight -2 div rlineto
            stroke            
        } if
        guardrightpos 0 ne {
            newpath
            guardrightpos x add guardwidth sub guardrightypos guardheight 2 div add moveto
            guardwidth guardheight -2 div rlineto
            guardwidth neg guardheight -2 div rlineto
            stroke            
        } if
    } if
    
    grestore
    
    end

} bind def
/renlinear load 0 1 dict put
% --END RENDERER renlinear--

% --BEGIN RENDERER renmatrix--
/renmatrix {

    0 begin

    /args exch def

    % Default options
    /width 1 def
    /height 1 def

    % Apply the renderer options
    args {exch cvlit exch def} forall

    % Parse the user options
    opt {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop
 
    /width width cvr def
    /height height cvr def

    % Convert the bits into a string
    /imgstr pixs length string def
    0 1 pixs length 1 sub {
        dup imgstr 3 1 roll pixs exch get 1 exch sub 255 mul put
    } for

    % Draw the image
    gsave
    currentpoint translate
    72 width mul 72 height mul scale
    pixx pixy 8 [ pixx 0 0 pixy neg 0 pixy ] {imgstr} image
    grestore

    end

} bind def
/renmatrix load 0 1 dict put
% --END RENDERER renmatrix--

% --BEGIN RENDERER renmaximatrix--
/renmaximatrix {

    0 begin

    /args exch def   % We are given some arguments

    % Apply the renderer options
    args {exch cvlit exch def} forall
 
    % Parse the user options   
    opt {
        token false eq {exit} if dup length string cvs (=) search
        true eq {cvlit exch pop exch def} {cvlit true def} ifelse
    } loop

    gsave

    currentpoint translate

    2.4945 dup scale  % from 1pt to 1.88mm
    0.5 0.5774 translate

    pixs {
        dup 
        /x exch 30 mod def 
        /y exch 30 idiv def
        y 2 mod 0 eq {x} {x 0.5 add} ifelse
        32 y sub 0.8661 mul
        moveto
        0     0.5774 rmoveto
        -0.5 -0.2887 rlineto
        0    -0.5774 rlineto
        0.5  -0.2887 rlineto
        0.5   0.2887 rlineto
        0     0.5774 rlineto
        -0.5  0.2887 rlineto
        closepath fill
    } forall

    % Plot the locator symbol
    newpath 14 13.8576 0.5774 0 360 arc closepath
    14 13.8576 1.3359 360 0 arcn closepath fill
    newpath 14 13.8576 2.1058 0 360 arc closepath
    14 13.8576 2.8644 360 0 arcn closepath fill
    newpath 14 13.8576 3.6229 0 360 arc closepath
    14 13.8576 4.3814 360 0 arcn closepath fill

    grestore

    end

} bind def
/renmaximatrix load 0 1 dict put
% --END RENDERER renmaximatrix--

% --BEGIN DISPATCHER--
/barcode {
    0 begin
    dup (ren) get cvx exec 
    end
} bind def
/barcode load 0 1 dict put
% --END DISPATCHER--

% --END TEMPLATE--
