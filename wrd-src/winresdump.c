#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <stdarg.h>
#include "wv_extract.h"
#include "newexe.h"

void DumpData(FILE *out,U32 pos,U32 len,FILE *fd);
void DumpICO(FILE *out,U32 pos,U32 len,FILE *fd);
void DumpCUR(FILE *out,U32 pos,U32 len,FILE *fd);
FILE *DumpBMPHeader(char *name,U32 len,FILE *fd);
void do_resource_dir(IMAGE_FILE_HEADER *peheader,IMAGE_SECTION_HEADER *section,FILE *ne,U32 offset,int level,U32 resourcetype);

#ifdef MIN
#undef MIN
#endif
#define MIN(a,b) (((a) < (b)) ? (a) : (b))

void wvRealTrace(char *file, int line, char * msg)
    {
#ifdef DEBUG
    fprintf(stderr, "wvTrace: (%s:%d) %s ",file,line, msg);
#endif
    }

extern char *winresdump_ver;

U16 globalshift = 1;

int main(int argc,char **argv)
	{
	FILE *ne;
	DOSHdr header;
	NEHrd neheader;
	IMAGE_FILE_HEADER peheader;
	IMAGE_OPTIONAL_HEADER ntOptHeader;
	IMAGE_SECTION_HEADER *section;
	ResourceTable resources;

	U16 i,j;
	U32 test;

	printf("%s\n",winresdump_ver);

	if (argc < 2)
		{
		printf("Usage: winresdump something.exe\n");
		return(1);
		}
	ne = fopen(argv[1],"rb");
	if (ne == NULL)
		{
		printf("Coundn't open file %s\n",argv[1]);
		return(1);
		}

	E_MAGIC(header) = read_16ubit(ne);
	if (E_MAGIC(header) != EMAGIC)
		{
		printf("%s is not a windows exe\n",argv[1]);
		fclose(ne);
		return(1);
		}
	rewind(ne);

	wvGetDOSHdr(&header,ne);
	fseek(ne,E_LFANEW(header),SEEK_SET);
	wvTrace(("%x\n",E_LFANEW(header)));
	wvGetNEHdr(&neheader,ne);
	if (NE_MAGIC(neheader) == NEMAGIC)
		{
		printf("Doing ne binary\n");
		if ( (NE_RESTAB(neheader) - NE_RSRCTAB(neheader)) == 0)
			{
			printf("No resources\n");
			fclose(ne);
			return(1);
			}

		if((NE_RSRCTAB(neheader) - NE_SEGTAB(neheader))%8!=0)
			printf("Warning - Extra 4 bytes in segment table.\n");

		
		fseek(ne,NE_RSRCTAB(neheader)+E_LFANEW(header),SEEK_SET);
		wvTrace(("seeking to %x\n",NE_RSRCTAB(neheader)+E_LFANEW(header)));
		wvGetResourceTable(&resources,ne);
		wvReleaseResourceTable(&resources);
		}
	else
		{
		fseek(ne,E_LFANEW(header),SEEK_SET);
		wvGetIMAGE_FILE_HEADER(&peheader,ne);
		if (peheader.signaturebytes != 0x00004550)
			{
			printf("file was neither a ne or pe file\n");
			fclose(ne);
			return(1);
			}
		printf("Doing pe binary\n");
		wvGetIMAGE_OPTIONAL_HEADER(&ntOptHeader,ne);
		section = (IMAGE_SECTION_HEADER *)malloc(sizeof(IMAGE_SECTION_HEADER)*peheader.NumberOfSections);
		for (i=0;i<peheader.NumberOfSections;i++)
			wvGetIMAGE_SECTION_HEADER(&section[i],ne);

		test = ImageDirectoryOffset (&peheader,&ntOptHeader, section,IMAGE_DIRECTORY_ENTRY_RESOURCE);

		fseek(ne,test,SEEK_SET);

		do_resource_dir(&peheader,section,ne,test,0,0);

		wvFree(section);
		}
	fclose(ne);
	return(0);
	}


void wvGetDOSHdr(DOSHdr *header,FILE *fd)
	{
	int i;
	header->e_magic = read_16ubit(fd);
	header->e_cblp = read_16ubit(fd);
	header->e_cp = read_16ubit(fd);
	header->e_crlc = read_16ubit(fd);
	header->e_cparhdr = read_16ubit(fd);
	header->e_minalloc = read_16ubit(fd);
	header->e_maxalloc = read_16ubit(fd);
	header->e_ss = read_16ubit(fd);
	header->e_sp = read_16ubit(fd);
	header->e_csum = read_16ubit(fd);
	header->e_ip = read_16ubit(fd);
	header->e_cs = read_16ubit(fd);
	header->e_lfarlc = read_16ubit(fd);
	header->e_ovno = read_16ubit(fd);
	for(i=0;i<ERES1WDS;i++)
		header->e_res[i] = read_16ubit(fd);
	header->e_oemid = read_16ubit(fd);
	header->e_oeminfo = read_16ubit(fd);
	for (i=0;i<ERES2WDS;i++)
		header->e_res2[i] = read_16ubit(fd);
	header->e_lfanew = read_32ubit(fd);
	}

void wvGetIMAGE_FILE_HEADER(IMAGE_FILE_HEADER*peheader,FILE *fd)
	{
	peheader->signaturebytes = read_32ubit(fd);
	peheader->Machine = read_16ubit(fd);
	peheader->NumberOfSections = read_16ubit(fd);
	peheader->TimeDateStamp = read_32ubit(fd);
	peheader->PointerToSymbolTable = read_32ubit(fd);
	peheader->NumberOfSymbols = read_32ubit(fd);
	peheader->SizeOfOptionalHeader = read_16ubit(fd);
	peheader->Characteristics = read_16ubit(fd);;
	}

void wvGetIMAGE_OPTIONAL_HEADER(IMAGE_OPTIONAL_HEADER *nt,FILE *fd)
	{
	U32 i;
	nt->Magic = read_16ubit(fd);
    nt->MajorLinkerVersion = getc(fd);
    nt->MinorLinkerVersion = getc(fd);
    nt->SizeOfCode = read_32ubit(fd); 
    nt->SizeOfInitializedData = read_32ubit(fd);
    nt->SizeOfUninitializedData = read_32ubit(fd);
    nt->AddressOfEntryPoint = read_32ubit(fd);
    nt->BaseOfCode = read_32ubit(fd); 
    nt->BaseOfData = read_32ubit(fd); 

    /* extra NT stuff */
    nt->ImageBase = read_32ubit(fd);
    nt->SectionAlignment = read_32ubit(fd);
    nt->FileAlignment = read_32ubit(fd);
    nt->MajorOperatingSystemVersion = read_16ubit(fd);
    nt->MinorOperatingSystemVersion = read_16ubit(fd);
    nt->MajorImageVersion = read_16ubit(fd);
    nt->MinorImageVersion = read_16ubit(fd);
    nt->MajorSubsystemVersion = read_16ubit(fd);
    nt->MinorSubsystemVersion = read_16ubit(fd);
    nt->Reserved1 = read_32ubit(fd); 
    nt->SizeOfImage = read_32ubit(fd);
    nt->SizeOfHeaders = read_32ubit(fd);
    nt->CheckSum = read_32ubit(fd); 
    nt->Subsystem = read_16ubit(fd); 
    nt->DllCharacteristics = read_16ubit(fd);
    nt->SizeOfStackReserve = read_32ubit(fd);
    nt->SizeOfStackCommit = read_32ubit(fd);
    nt->SizeOfHeapReserve = read_32ubit(fd);
    nt->SizeOfHeapCommit = read_32ubit(fd);
    nt->LoaderFlags = read_32ubit(fd);
    nt->NumberOfRvaAndSizes = read_32ubit(fd);
	nt->DataDirectory = (IMAGE_DATA_DIRECTORY *)malloc(sizeof(IMAGE_DATA_DIRECTORY)*nt->NumberOfRvaAndSizes);
	for (i=0;i<nt->NumberOfRvaAndSizes;i++)
		wvGetIMAGE_DATA_DIRECTORY(&nt->DataDirectory[i],fd);
	}

void wvGetNEHdr(NEHrd *neheader,FILE *fd)
	{
	int i;
	neheader->ne_magic = read_16ubit(fd);
	neheader->ne_ver = getc(fd);   
	neheader->ne_rev = getc(fd);    
	neheader->ne_enttab = read_16ubit(fd); 
	neheader->ne_cbenttab = read_16ubit(fd);
	neheader->ne_crc = read_32ubit(fd);
	neheader->ne_flags = read_16ubit(fd);  
	neheader->ne_autodata = read_16ubit(fd);
	neheader->ne_heap = read_16ubit(fd);
	neheader->ne_stack = read_16ubit(fd);
	neheader->ne_csip = read_32ubit(fd);
	neheader->ne_sssp = read_32ubit(fd);
	neheader->ne_cseg = read_16ubit(fd);  
	neheader->ne_cmod = read_16ubit(fd);   
	neheader->ne_cbnrestab = read_16ubit(fd);
	neheader->ne_segtab = read_16ubit(fd); 
	neheader->ne_rsrctab = read_16ubit(fd);
	neheader->ne_restab = read_16ubit(fd);
	neheader->ne_modtab = read_16ubit(fd);
	neheader->ne_imptab = read_16ubit(fd);
	neheader->ne_nrestab = read_32ubit(fd);    
	neheader->ne_cmovent = read_16ubit(fd);
	neheader->ne_align = read_16ubit(fd);
	neheader->ne_cres = read_16ubit(fd);
	neheader->ne_exetyp = getc(fd); 
	neheader->ne_addflags = getc(fd);
	for (i=0;i<NERESWORDS;i++)
		neheader->ne_res[i] = read_16ubit(fd);
	neheader->ne_sdkrev = getc(fd);
	neheader->ne_sdkver = getc(fd);
	}

int wvGetTYPEINFO(TYPEINFO *t,FILE *fd)
	{
	int i;
	U16 test=0;
	char buffer[128];
	static int r,s,c,d;
	FILE *out;

	t->rtTypeID = read_16ubit(fd);
	wvTrace(("the type is %x\n",t->rtTypeID));
	if (t->rtTypeID & 0x8000)
		{
		test = t->rtTypeID&0x7fff;
		wvTrace(("the actual type is %d\n",test));
		}
	t->rtResourceCount = read_16ubit(fd);
	if ( (t->rtResourceCount == 0) || (t->rtTypeID == 0) )		/* !!? */
		{
		fseek(fd,-4,SEEK_CUR);
		wvTrace(("aborting TYPEINFO list\n"));
		return(1);
		}
	t->rtReserved = read_32ubit(fd);
	if (t->rtResourceCount == 0)
		t->rtNameInfo = NULL;
	else
		t->rtNameInfo = malloc(sizeof(NAMEINFO)*t->rtResourceCount);
	wvTrace(("rtResourceCount is %d\n",t->rtResourceCount));
	for (i=0;i<t->rtResourceCount;i++)
		{
		wvGetNAMEINFO(&t->rtNameInfo[i],fd);
		wvTrace(("the offset is %x, len %d\n",t->rtNameInfo[i].rnOffset,t->rtNameInfo[i].rnLength));
		switch(test)
			{
			case RT_BITMAP:
				r++;
				sprintf(buffer,"bitmap%d.bmp",r);
				printf("Dumping bitmap resource %s\n",buffer);
				out = DumpBMPHeader(buffer,t->rtNameInfo[i].rnLength*pow(2,globalshift),fd);
				DumpData(out,t->rtNameInfo[i].rnOffset*pow(2,globalshift),t->rtNameInfo[i].rnLength*pow(2,globalshift),fd);
				break;
			case RT_CURSOR:
				c++;
				sprintf(buffer,"cursor%d.bmp",c);
				printf("Dumping cursor resource %s\n",buffer);
				out = DumpBMPHeader(buffer,t->rtNameInfo[i].rnLength*pow(2,globalshift),fd);
				DumpCUR(out,t->rtNameInfo[i].rnOffset*pow(2,globalshift),t->rtNameInfo[i].rnLength*pow(2,globalshift),fd);
				break;
			case RT_ICON:
				s++;
				sprintf(buffer,"icon%d.bmp",s);
				printf("Dumping icon resource %s\n",buffer);
				out = DumpBMPHeader(buffer,t->rtNameInfo[i].rnLength*pow(2,globalshift),fd);
				DumpICO(out,t->rtNameInfo[i].rnOffset*pow(2,globalshift),t->rtNameInfo[i].rnLength*pow(2,globalshift),fd);
				break;
			case RT_DIALOG:
				d++;
				sprintf(buffer,"dialog%d.dlg",d);
				printf("Dumping dialog resource %s\n",buffer);
				out = fopen(buffer,"wb");
				DumpData(out,t->rtNameInfo[i].rnOffset*pow(2,globalshift),t->rtNameInfo[i].rnLength*pow(2,globalshift),fd);
				break;
			/* 
			all the other RT_ resources are listed in newexe.h and their internal format is
			in doc/resfmt.txt, read the webpage as to what you could do with them
			*/
			}
		}
	return(0);
	}
	
void wvReleaseTYPEINFO(TYPEINFO *t)
	{
	wvFree(t->rtNameInfo);
	}

void wvGetNAMEINFO(NAMEINFO *n,FILE *fd)
	{
	n->rnOffset = read_16ubit(fd);
	n->rnLength = read_16ubit(fd);
	n->rnFlags = read_16ubit(fd);
	n->rnID = read_16ubit(fd);
	n->rnHandle = read_16ubit(fd);
	n->rnUsage = read_16ubit(fd);
	}


void wvGetResourceTable(ResourceTable *r,FILE *fd)
	{
	int i;
	U8 mychar;
	int len;
	int noofstring;
	int totalstr;
	r->rscAlignShift = read_16ubit(fd);
	globalshift = r->rscAlignShift;
	wvTrace(("rscAlignShift %d\n",r->rscAlignShift));
	r->rscTypes = malloc(sizeof(TYPEINFO) * 10);
	for (i=0;i<10;i++)
		{
		wvTrace(("before pos is %x\n",ftell(fd)));
		if (1 == wvGetTYPEINFO(&r->rscTypes[i],fd))
			break;
		wvTrace(("after pos is %x\n",ftell(fd)));
		}
	wvTrace(("final pos is %x\n",ftell(fd)));
    r->rscEndTypes=read_16ubit(fd);

	mychar = getc(fd);
	r->rscResourceNames = (char **)malloc(sizeof(char *)*10);
	totalstr=10;
	noofstring=0;
	
	while(mychar != 0)
		{
		len = mychar;
		if (noofstring == totalstr)
			{
			totalstr+=10;
			r->rscResourceNames = (char **)realloc(r->rscResourceNames,sizeof(char *)*totalstr);
			}
		r->rscResourceNames[noofstring] = (char *)malloc(len+1);
		for (i=0;i<len;i++)
	    	r->rscResourceNames[noofstring][i] = getc(fd);
	    r->rscResourceNames[noofstring][i] = 0;
		noofstring++;
		mychar = getc(fd);
		}

    r->rscEndNames = mychar;

	for (i=0;i<noofstring;i++)
		wvTrace(("string was %s\n",r->rscResourceNames[i]));
	}

void wvReleaseResourceTable(ResourceTable *r)
	{
	wvFree(r->rscTypes);
	}

FILE *DumpBMPHeader(char *name,U32 len,FILE *fd)
	{
	FILE *out;
	U32 size;
	out = fopen(name,"w+b");
	fputc('B',out);
	fputc('M',out);
	size = len+14;
	wvTrace(("len size %d %d\n",size,len));
	write_32ubit(size,out);
	fputc(0,out);
	fputc(0,out);
	fputc(0,out);
	fputc(0,out);
	write_32ubit(0x3e,out);
	return(out);
	}

void DumpData(FILE *out,U32 pos,U32 len,FILE *fd)
	{
	int i;
	long p = ftell(fd);
	fseek(fd,pos,SEEK_SET);
	for (i=0;i<len;i++)
		fputc(getc(fd),out);
	fclose(out);
	fseek(fd,p,SEEK_SET);
	}

void DumpICO(FILE *out,U32 pos,U32 len,FILE *fd)
	{
	int i;
	U32 h;
	long p = ftell(fd);
	fseek(fd,pos,SEEK_SET);
	for (i=0;i<8;i++)
		fputc(getc(fd),out);
	h = read_32ubit(fd);
	write_32ubit(h/2,out);
	for (i=0;i<len-12;i++)
		fputc(getc(fd),out);
	fclose(out);
	fseek(fd,p,SEEK_SET);
	}

void DumpCUR(FILE *out,U32 pos,U32 len,FILE *fd)
	{
	int i;
	U32 h;
	long p = ftell(fd);
	fseek(fd,pos,SEEK_SET);
	for (i=0;i<4;i++)
		getc(fd);
	for (i=0;i<8;i++)
		fputc(getc(fd),out);
	h = read_32ubit(fd);
	write_32ubit(h/2,out);
	for (i=0;i<len-16;i++)
		fputc(getc(fd),out);
	fclose(out);
	fseek(fd,p,SEEK_SET);
	}


void wvGetIMAGE_DATA_DIRECTORY(IMAGE_DATA_DIRECTORY *id,FILE *fd)
	{
	id->VirtualAddress = read_32ubit(fd);
	id->Size = read_32ubit(fd);
	}


U32 ImageDirectoryOffset (IMAGE_FILE_HEADER *hdr,IMAGE_OPTIONAL_HEADER *poh, IMAGE_SECTION_HEADER *psh,U32 dwIMAGE_DIRECTORY)
{
    U16 nSections = hdr->NumberOfSections;
    int i = 0;
    U32 VAImageDir;

    /* Must be 0 thru (NumberOfRvaAndSizes-1). */
    if (dwIMAGE_DIRECTORY >= poh->NumberOfRvaAndSizes)
        return 0xffffffff;

    /* Locate image directory's relative virtual address. */
    VAImageDir = poh->DataDirectory[dwIMAGE_DIRECTORY].VirtualAddress;

    /* Locate section containing image directory. */
    while (i++<nSections)
        {
        if (psh->VirtualAddress <= VAImageDir &&
            psh->VirtualAddress + 
                 psh->SizeOfRawData > VAImageDir)
            break;
        psh++;
        }

    if (i > nSections)
        return 0xffffffff;

    /* Return image import directory offset. */
    return (VAImageDir - psh->VirtualAddress + psh->PointerToRawData);
}

U32 VirtualToReal (IMAGE_FILE_HEADER *hdr,U32 VAImageDir,IMAGE_SECTION_HEADER *psh)
{
    U16 nSections = hdr->NumberOfSections;
    int i = 0;

    /* Locate section containing image directory. */
    while (i++<nSections)
        {
        if (psh->VirtualAddress <= VAImageDir &&
            psh->VirtualAddress + 
                 psh->SizeOfRawData > VAImageDir)
            break;
        psh++;
        }

    if (i > nSections)
        return 0xffffffff;

    /* Return image import directory offset. */
    return (VAImageDir - psh->VirtualAddress + psh->PointerToRawData);
}

void wvGetIMAGE_SECTION_HEADER(IMAGE_SECTION_HEADER *h,FILE *fd)
	{
	int i;
	for (i=0;i<IMAGE_SIZEOF_SHORT_NAME;i++)
		h->Name[i] = getc(fd);
	h->Misc.VirtualSize=read_32ubit(fd);
    h->VirtualAddress=read_32ubit(fd);
    h->SizeOfRawData=read_32ubit(fd);
    h->PointerToRawData=read_32ubit(fd);
    h->PointerToRelocations=read_32ubit(fd);
    h->PointerToLinenumbers=read_32ubit(fd);
    h->NumberOfRelocations=read_16ubit(fd);
    h->NumberOfLinenumbers=read_16ubit(fd);
    h->Characteristics=read_32ubit(fd);
	}

void wvGetIMAGE_RESOURCE_DIRECTORY(IMAGE_RESOURCE_DIRECTORY *id,FILE *fd)
	{
	id->Characteristics = read_32ubit(fd);
    id->TimeDateStamp = read_32ubit(fd);
    id->MajorVersion = read_16ubit(fd);
    id->MinorVersion = read_16ubit(fd);
    id->NumberOfNamedEntries = read_16ubit(fd);
    id->NumberOfIdEntries = read_16ubit(fd);
	}

void wvGetIMAGE_RESOURCE_DIRECTORY_ENTRY(IMAGE_RESOURCE_DIRECTORY_ENTRY *ie,FILE *fd)
	{
	ie->Name = read_32ubit(fd);
	ie->OffsetToData = read_32ubit(fd);
	}

void wvGetIMAGE_RESOURCE_DATA_ENTRY(IMAGE_RESOURCE_DATA_ENTRY *de,FILE *fd)
    {
    de->OffsetToData = read_32ubit(fd);
    de->Size = read_32ubit(fd);
    de->CodePage = read_32ubit(fd);
    de->Reserved = read_32ubit(fd);
    } 

/* The predefined resource types */
char *SzResourceTypes[] = {
"???_0", "CURSOR", "BITMAP", "ICON", "MENU", "DIALOG", "STRING", "FONTDIR",
"FONT", "ACCELERATORS", "RCDATA", "MESSAGETABLE", "GROUP_CURSOR",
"???_13", "GROUP_ICON", "???_15", "VERSION","DLGINCLUDE","???_18","PLUGPLAY","VXD",
"ANICURSOR"
};

/* Get an ASCII string representing a resource type */
void GetResourceTypeName(U32 type, char *buffer, int cBytes)
	{
	if ( type <= 16 )
		strncpy(buffer, SzResourceTypes[type], cBytes);
	else
		sprintf(buffer, "%x", type);
	}

/*
If a resource entry has a string name (rather than an ID), go find
the string and convert it from unicode to ascii.
*/
void GetResourceNameFromId (U32 id, char *buffer, int cBytes, FILE *ne, U32 orig)
	{
	U16 len,i;
	wchar_t *pwcs=NULL;
	size_t pos;
	long cur=ftell(ne);

    // If it's a regular ID, just format it.
    if ( !(id & IMAGE_RESOURCE_NAME_IS_STRING) )
    	{
        sprintf(buffer, "%x", id);
        return;
    	}

    id &= 0x7FFFFFFF;

	fseek(ne,orig+=id,SEEK_SET);
#if 0
    prdsu = (PIMAGE_RESOURCE_DIR_STRING_U)(resourceBase + id);

    /* prdsu->Length is the number of unicode characters*/
    WideCharToMultiByte(CP_ACP, 0, prdsu->NameString, prdsu->Length,
                        buffer, cBytes, 0, 0);
#endif
	len = read_16ubit(ne);
	pwcs = (wchar_t *)malloc(sizeof(wchar_t)*len+1);
	for(i=0;i<len;i++)
		pwcs[i] = read_16ubit(ne);

	pos = wcstombs(buffer, pwcs, cBytes);
	if (pos != -1) buffer[pos] = 0;

    buffer[ MIN(cBytes-1,len) ] = 0;  /* Null terminate it!!!*/
	wvFree(pwcs);
	fseek(ne,cur,SEEK_SET);
	}



void do_resource_dir(IMAGE_FILE_HEADER *peheader,IMAGE_SECTION_HEADER *section,FILE *ne, U32 origoffset,int level,U32 resourceType)
	{
	char szType[64];
	IMAGE_RESOURCE_DIRECTORY id;
	IMAGE_RESOURCE_DIRECTORY_ENTRY *ie;
	IMAGE_RESOURCE_DATA_ENTRY de;
	U32 i,offset,j;
	long pos;
	char buffer[128];
	static int r,s,c,d;
	FILE *out;
	static int lastres;

	wvTrace(("getting dir at %x\n",ftell(ne)));
	wvGetIMAGE_RESOURCE_DIRECTORY(&id,ne);

	wvTrace(("there are %d entries\n",id.NumberOfNamedEntries + id.NumberOfIdEntries));

	for ( i=0; i < level; i++ ) printf("    ");

	if ( level == 1 && !(resourceType & IMAGE_RESOURCE_NAME_IS_STRING) )
		{
        GetResourceTypeName( resourceType, szType, sizeof(szType) );
		lastres = resourceType;
		}
	else
		GetResourceNameFromId( resourceType, szType, sizeof(szType),ne,origoffset);

	printf( "ResDir (%s) Named:%02x ID:%02x TimeDate:%08x Vers:%u.%02u Char:%x\n",
				szType, id.NumberOfNamedEntries, id.NumberOfIdEntries,
				id.TimeDateStamp, id.MajorVersion,
				id.MinorVersion,id.Characteristics);

	ie = (IMAGE_RESOURCE_DIRECTORY_ENTRY*)malloc(sizeof(IMAGE_RESOURCE_DIRECTORY_ENTRY)*(id.NumberOfNamedEntries + id.NumberOfIdEntries));

	for (i=0;i<id.NumberOfNamedEntries + id.NumberOfIdEntries;i++)
		{
		wvTrace(("getting IMAGE_RESOURCE_DIRECTORY_ENTRY %x\n",ftell(ne)));
		wvGetIMAGE_RESOURCE_DIRECTORY_ENTRY(&ie[i],ne);
		pos = ftell(ne);
		offset = ie[i].OffsetToData & IMAGE_RESOURCE_DATA_IS_DIRECTORY;
		if (offset)
			{
			offset = ie[i].OffsetToData & 0x7FFFFFFFL;
			offset = offset+origoffset;
			fseek(ne,offset,SEEK_SET);
			wvTrace(("really going to %x\n",offset));
			do_resource_dir(peheader,section,ne,origoffset,level+1,ie[i].Name);
			}
		else
			{
			for ( j=0; j < level+1; j++ ) printf("    ");
			printf("ID: 0x%x Offset:0x%x",ie[i].Name,ie[i].OffsetToData);
			fseek(ne,ie[i].OffsetToData+origoffset,SEEK_SET);
			wvTrace(("seeking to %x\n",ie[i].OffsetToData+origoffset));
			wvGetIMAGE_RESOURCE_DATA_ENTRY(&de,ne);
			printf(" Data Offset:0x%x (Real 0x%x) Size:%d)\n",de.OffsetToData,VirtualToReal (peheader,de.OffsetToData,section),de.Size);
			if (de.Size <= 0)
				continue;
			switch(lastres)
				{
				case RT_BITMAP:
					sprintf(buffer,"bitmap%d.bmp",r++);
					printf("Dumping bitmap resource %s\n",buffer);
					out = DumpBMPHeader(buffer,de.Size,ne);
					DumpData(out,VirtualToReal (peheader,de.OffsetToData,section),de.Size,ne);
					break;
				case RT_CURSOR:
					sprintf(buffer,"cursor%d.bmp",s++);
					printf("Dumping cursor resource %s\n",buffer);
					out = DumpBMPHeader(buffer,de.Size,ne);
					DumpCUR(out,VirtualToReal (peheader,de.OffsetToData,section),de.Size,ne);
					break;
				case RT_ICON:
					sprintf(buffer,"icon%d.bmp",c++);
					printf("Dumping icon resource %s\n",buffer);
					out = DumpBMPHeader(buffer,de.Size,ne);
					DumpICO(out,VirtualToReal (peheader,de.OffsetToData,section),de.Size,ne);
					break;
				case RT_DIALOG:
					sprintf(buffer,"dialog%d.dlg",d++);
					printf("Dumping dialog resource %s\n",buffer);
					out = fopen(buffer,"wb");
					DumpData(out,VirtualToReal (peheader,de.OffsetToData,section),de.Size,ne);
					break;
				/* 
				all the other RT_ resources are listed in newexe.h and their internal format is
				in doc/resfmt.txt, read the webpage as to what you could do with them
				*/
				}
			}
		fseek(ne,pos,SEEK_SET);
		}
	wvFree(ie);
	}

char * wvFmtMsg(char *fmt, ...)
    {
    static char mybuf[1024];

    va_list argp;
    va_start(argp, fmt);
    vsprintf(mybuf, fmt, argp);
    va_end(argp);

    return mybuf;
	}

