/*
Released under GPL, written by Caolan.McNamara@ul.ie.

Copyright (C) 1998,1999 
	Caolan McNamara

Real Life: Caolan McNamara           *  Doing: MSc in HCI
Work: Caolan.McNamara@ul.ie          *  Phone: +353-86-8790257
URL: http://skynet.csn.ul.ie/~caolan *  Sig: an oblique strategy
How would you have done it?
*/

#include <stdio.h>
#include <stdlib.h>
#include "wv_extract.h"

void write_32ubit(U32 chunk,FILE *in)
	{
	U16 temp1,temp2;
	temp1 = chunk & 0x0000ffff;
	temp2 = (chunk >> 16) & 0x0000ffff;
	write_16ubit(temp1,in);
	write_16ubit(temp2,in); 
	}


U32 read_32ubit(FILE *in)
	{
	U16 temp1,temp2;
	U32 ret;
	temp1 = read_16ubit(in);
	temp2 = read_16ubit(in); 
	ret = temp2;
	ret = ret << 16;
	ret += temp1;
	return(ret);
	}

void write_16ubit(U16 chunk,FILE *in)
	{
	U8 temp1,temp2;
	
	temp1 = chunk & 0x00ff;
	temp2 = (chunk >> 8) & 0x00ff;
	fputc(temp1,in);
	fputc(temp2,in);
	}

U16 read_16ubit(FILE *in)
	{
	U8 temp1,temp2;
	U16 ret;
	temp1 = getc(in);
	temp2 = getc(in);
	ret = temp2;
	ret = ret << 8;
	ret += temp1;
	return(ret);
	}

void wvFree(void *ptr)
    {
    if (ptr != NULL)
        free(ptr);
    ptr = NULL;
    }

