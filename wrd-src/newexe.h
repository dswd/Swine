  /*
   *	  NEWEXE.H (C) Copyright Microsoft Corp 1984-1987
   *
   *	  Data structure definitions for the OS/2 & Windows
   *	  executable file format.
   *
   *	  Modified by IVS on 24-Jan-1991 for Resource DeCompiler
   *	  (C) Copyright IVS 1991
   *
   *
   */

  #define EMAGIC	  0x5A4D	  /* Old magic number */
  #define ENEWEXE	  sizeof(DOSHdr)
					  /* Value of E_LFARLC for new .EXEs */
  #define ENEWHDR	  0x003C	  /* Offset in old hdr. of ptr. to new */
  #define ERESWDS	  0x0010	  /* No. of reserved words (OLD) */
  #define ERES1WDS	  0x0004	  /* No. of reserved words in e_res */
  #define ERES2WDS	  0x000A	  /* No. of reserved words in e_res2 */
  #define ECP		  0x0004	  /* Offset in struct of E_CP */
  #define ECBLP 	  0x0002	  /* Offset in struct of E_CBLP */
  #define EMINALLOC	  0x000A	  /* Offset in struct of E_MINALLOC */

  typedef struct exe_hdr			  /* DOS 1, 2, 3 .EXE header */
    {
      U16	  e_magic;	  /* 00 Magic number */
      U16	  e_cblp;	  /* 02 Bytes on last page of file */
      U16	  e_cp; 	  /* 04 Pages in file */
      U16	  e_crlc;	  /* 06 Relocations */
      U16	  e_cparhdr;	  /* 08 Size of header in paragraphs */
      U16	  e_minalloc;	  /* 0A Minimum extra paragraphs needed */
      U16	  e_maxalloc;	  /* 0C Maximum extra paragraphs needed */
      U16	  e_ss; 	  /* 0E Initial (relative) SS value */
      U16	  e_sp; 	  /* 10 Initial SP value */
      U16	  e_csum;	  /* 12 Checksum */
      U16	  e_ip; 	  /* 14 Initial IP value */
      U16	  e_cs; 	  /* 16 Initial (relative) CS value */
      U16	  e_lfarlc;	  /* 18 File address of relocation table */
      U16	  e_ovno;	  /* 1A Overlay number */
      U16	  e_res[ERES1WDS];/* 1C Reserved words */
      U16	  e_oemid;	  /* 24 OEM identifier (for e_oeminfo) */
      U16	  e_oeminfo;	  /* 26 OEM information; e_oemid specific */
      U16	  e_res2[ERES2WDS];/*28 Reserved words */
      U32     e_lfanew;	  /* 3C File address of new exe header */
    } DOSHdr;					  /* 40h size of structure */

  #define E_MAGIC(x)	  (x).e_magic
  #define E_CBLP(x)	  (x).e_cblp
  #define E_CP(x)	  (x).e_cp
  #define E_CRLC(x)	  (x).e_crlc
  #define E_CPARHDR(x)	  (x).e_cparhdr
  #define E_MINALLOC(x)   (x).e_minalloc
  #define E_MAXALLOC(x)   (x).e_maxalloc
  #define E_SS(x)	  (x).e_ss
  #define E_SP(x)	  (x).e_sp
  #define E_CSUM(x)	  (x).e_csum
  #define E_IP(x)	  (x).e_ip
  #define E_CS(x)	  (x).e_cs
  #define E_LFARLC(x)	  (x).e_lfarlc
  #define E_OVNO(x)	  (x).e_ovno
  #define E_RES(x)	  (x).e_res
  #define E_OEMID(x)	  (x).e_oemid
  #define E_OEMINFO(x)	  (x).e_oeminfo
  #define E_RES2(x)	  (x).e_res2
  #define E_LFANEW(x)	  (x).e_lfanew

  #define NEMAGIC	  0x454E	  /* New magic number */
  #define NERESWORDS	  3		  /* 6 bytes reserved */
  #define NECRC 	  8		  /* Offset into new header of NE_CRC */

  typedef struct new_exe			  /* New .EXE header */
    {
      U16	  ne_magic;	  /* 00 Magic number NE_MAGIC */
      U8	  ne_ver;	  /* 02 Linker Version number */
      U8	  ne_rev;	  /* 03 Linker Revision number */
      U16	  ne_enttab;	  /* 04 Offset of Entry Table */
      U16	  ne_cbenttab;	  /* 06 Number of bytes in Entry Table */
      U32		  ne_crc;	  /* 08 Checksum of whole file */
      U16	  ne_flags;	  /* 0C Flag word */
      U16	  ne_autodata;	  /* 0E Automatic data segment number */
      U16	  ne_heap;	  /* 10 Initial heap allocation */
      U16	  ne_stack;	  /* 12 Initial stack allocation */
      U32		  ne_csip;	  /* 14 Initial CS:IP setting */
      U32		  ne_sssp;	  /* 18 Initial SS:SP setting */
      U16	  ne_cseg;	  /* 1C Count of file segments */
      U16	  ne_cmod;	  /* 1E Entries in Module Reference Table */
      U16	  ne_cbnrestab;   /* 20 Size of non-resident name table */
      U16	  ne_segtab;	  /* 22 Offset of Segment Table */
      U16	  ne_rsrctab;	  /* 24 Offset of Resource Table */
      U16	  ne_restab;	  /* 26 Offset of resident name table */
      U16	  ne_modtab;	  /* 28 Offset of Module Reference Table */
      U16	  ne_imptab;	  /* 2A Offset of Imported Names Table */
      U32		  ne_nrestab;	  /* 2C Offset of Non-resident Names Table */
      U16	  ne_cmovent;	  /* 30 Count of movable entries */
      U16	  ne_align;	  /* 32 Segment alignment shift count */
      U16	  ne_cres;	  /* 34 Count of resource entries */
      U8	  ne_exetyp;	  /* 36 Target operating system */
      U8	  ne_addflags;	  /* 37 Additional flags */
      U16	  ne_res[NERESWORDS]; /* 38 3 reserved words */
      U8	  ne_sdkrev;	  /* 3E Windows SDK revison number */
      U8	  ne_sdkver;	  /* 3F Windows SDK version number */
    } NEHrd;

  #define NE_MAGIC(x)	  (x).ne_magic
  #define NE_VER(x)	  (x).ne_ver
  #define NE_REV(x)	  (x).ne_rev
  #define NE_ENTTAB(x)	  (x).ne_enttab
  #define NE_CBENTTAB(x)  (x).ne_cbenttab
  #define NE_CRC(x)	  (x).ne_crc
  #define NE_FLAGS(x)	  (x).ne_flags
  #define NE_AUTODATA(x)  (x).ne_autodata
  #define NE_HEAP(x)	  (x).ne_heap
  #define NE_STACK(x)	  (x).ne_stack
  #define NE_CSIP(x)	  (x).ne_csip
  #define NE_SSSP(x)	  (x).ne_sssp
  #define NE_CSEG(x)	  (x).ne_cseg
  #define NE_CMOD(x)	  (x).ne_cmod
  #define NE_CBNRESTAB(x) (x).ne_cbnrestab
  #define NE_SEGTAB(x)	  (x).ne_segtab
  #define NE_RSRCTAB(x)   (x).ne_rsrctab
  #define NE_RESTAB(x)	  (x).ne_restab
  #define NE_MODTAB(x)	  (x).ne_modtab
  #define NE_IMPTAB(x)	  (x).ne_imptab
  #define NE_NRESTAB(x)   (x).ne_nrestab
  #define NE_CMOVENT(x)   (x).ne_cmovent
  #define NE_ALIGN(x)	  (x).ne_align
  #define NE_CRES(x)	  (x).ne_cres
  #define NE_RES(x)	  (x).ne_res
  #define NE_EXETYP(x)	  (x).ne_exetyp
  #define NE_ADDFLAGS(x)  (x).ne_addflags
  #define NE_SDKVER(x)	  (x).ne_sdkver
  #define NE_SDKREV(x)	  (x).ne_sdkrev

  #define NE_USAGE(x)	  (WORD)*((WORD *)(x)+1)
  #define NE_PNEXTEXE(x)  (WORD)(x).ne_cbenttab
  #define NE_ONEWEXE(x)   (WORD)(x).ne_crc
  #define NE_PFILEINFO(x) (WORD)((DWORD)(x).ne_crc >> 16)


  /*
   *  Target operating systems
   */

  #define NE_UNKNOWN	  0x0		  /* Unknown (any "new-format" OS) */
  #define NE_OS2	  0x1		  /* Microsoft/IBM OS/2 (default)  */
  #define NE_WINDOWS	  0x2		  /* Microsoft Windows */
  #define NE_DOS4	  0x3		  /* Microsoft MS-DOS 4.x */
  #define NE_WIN386	  0x4		  /* Windows 386  ????????? */

  /*
   *  Format of NE_FLAGS(x):
   *
   *  p 				  Not-a-process
   *   x				  Unused
   *	e				  Errors in image
   *	 x				  Unused
   *	  b				  Bound as family app
   *	   ttt				  Application type
   *	      f 			  Floating-point instructions
   *	       3			  386 instructions
   *		2			  286 instructions
   *		 0			  8086 instructions
   *		  P			  Protected mode only
   *		   p			  Per-process library initialization
   *		    i			  Instance data
   *		     s			  Solo data
   */
  #define NENOTP	  0x8000	  /* Not a process */
  #define NEIERR	  0x2000	  /* Errors in image */
  #define NEBOUND	  0x0800	  /* Bound as family app */
  #define NEAPPTYP	  0x0700	  /* Application type mask */
  #define NENOTWINCOMPAT  0x0100	  /* Not compatible with P.M. Windowing */
  #define NEWINCOMPAT	  0x0200	  /* Compatible with P.M. Windowing */
  #define NEWINAPI	  0x0300	  /* Uses P.M. Windowing API */
  #define NEFLTP	  0x0080	  /* Floating-point instructions */
  #define NEI386	  0x0040	  /* 386 instructions */
  #define NEI286	  0x0020	  /* 286 instructions */
  #define NEI086	  0x0010	  /* 8086 instructions */
  #define NEPROT	  0x0008	  /* Runs in protected mode only */
  #define NEPPLI	  0x0004	  /* Per-Process Library Initialization */
  #define NEINST	  0x0002	  /* Instance data */
  #define NESOLO	  0x0001	  /* Solo data */


  struct new_seg			  /* New .EXE segment table entry */
    {
      U16	  ns_sector;	  /* File sector of start of segment */
      U16	  ns_cbseg;	  /* Number of bytes in file */
      U16	  ns_flags;	  /* Attribute flags */
      U16	  ns_minalloc;	  /* Minimum allocation in bytes */
    };
  #define NS_SECTOR(x)	  (x).ns_sector
  #define NS_CBSEG(x)	  (x).ns_cbseg
  #define NS_FLAGS(x)	  (x).ns_flags
  #define NS_MINALLOC(x)  (x).ns_minalloc

  /*
   *
   *  x 			  Unused
   *   h			  Huge segment
   *	c			  32-bit code segment
   *	 d			  Discardable segment
   *	  DD			  I/O privilege level (286 DPL bits)
   *	    c			  Conforming segment
   *	     r			  Segment has relocations
   *	      e 		  Execute/read only
   *	       p		  Preload segment
   *		P		  Pure segment
   *		 m		  Movable segment
   *		  i		  Iterated segment
   *		   ttt		  Segment type
   */
  #define NSTYPE	  0x0007	  /* Segment type mask */
  #define NSCODE	  0x0000	  /* Code segment */
  #define NSDATA	  0x0001	  /* Data segment */
  #define NSITER	  0x0008	  /* Iterated segment flag */
  #define NSMOVE	  0x0010	  /* Movable segment flag */
  #define NSSHARED	  0x0020	  /* Shared segment flag */
  #define NSPRELOAD	  0x0040	  /* Preload segment flag */
  #define NSEXRD	  0x0080	  /* Execute-only (code segment), or
					   *  read-only (data segment)
					   */
  #define NSRELOC	  0x0100	  /* Segment has relocations */
  #define NSCONFORM	  0x0200	  /* Conforming segment */
  #define NSDPL 	  0x0C00	  /* I/O privilege level (286 DPL bits) */
  #define SHIFTDPL	  10		  /* Left shift count for SEGDPL field */
  #define NSDISCARD	  0x1000	  /* Segment is discardable */
  #define NS32BIT	  0x2000	  /* 32-bit code segment */
  #define NSHUGE	  0x4000	  /* Huge memory segment, length of
					   * segment and minimum allocation
					   * size are in segment sector units
					   */
  #define NSPURE	  NSSHARED	  /* For compatibility */

  #define NSALIGN 9	  /* Segment data aligned on 512 byte boundaries */

  #define NSLOADED    0x0004	  /* ns_sector field contains memory addr */
  struct new_segdata			  /* Segment data */
    {
      union
	{
	  struct
	    {
	      U16	  ns_niter;	  /* number of iterations */
	      U16	  ns_nbytes;	  /* number of bytes */
	      char		  ns_iterdata;	  /* iterated data bytes */
	    } ns_iter;
	  struct
	    {
	      char		  ns_data;	  /* data bytes */
	    } ns_noniter;
	} ns_union;
    };

  struct new_rlcinfo			  /* Relocation info */
    {
      U16	  nr_nreloc;	  /* number of relocation items that */
    };					  /* follow */

  struct new_rlc			  /* Relocation item */
    {
      char		  nr_stype;	  /* Source type */
      char		  nr_flags;	  /* Flag byte */
      U16	  nr_soff;	  /* Source offset */
      union
	{
	  struct
	    {
	      char	  nr_segno;	  /* Target segment number */
	      char	  nr_res;	  /* Reserved */
	      U16 nr_entry;	  /* Target Entry Table offset */
	    }		  nr_intref;	  /* Internal reference */
	  struct
	    {
	      U16 nr_mod;	  /* Index into Module Reference Table */
	      U16 nr_proc;	  /* Procedure ordinal or name offset */
	    }		  nr_import;	  /* Import */
	  struct
	    {
	      U16 nr_ostype;   /* OSFIXUP type */
	      U16 nr_osres;	  /* reserved */
	    }		  nr_osfix;	  /* Operating system fixup */
	}		  nr_union;	  /* Union */
    };
  #define NR_STYPE(x)	  (x).nr_stype
  #define NR_FLAGS(x)	  (x).nr_flags
  #define NR_SOFF(x)	  (x).nr_soff
  #define NR_SEGNO(x)	  (x).nr_union.nr_intref.nr_segno
  #define NR_RES(x)	  (x).nr_union.nr_intref.nr_res
  #define NR_ENTRY(x)	  (x).nr_union.nr_intref.nr_entry
  #define NR_MOD(x)	  (x).nr_union.nr_import.nr_mod
  #define NR_PROC(x)	  (x).nr_union.nr_import.nr_proc
  #define NR_OSTYPE(x)	  (x).nr_union.nr_osfix.nr_ostype
  #define NR_OSRES(x)	  (x).nr_union.nr_osfix.nr_osres

  /*
   *  Format of NR_STYPE(x):
   *
   *  xxxxx				  Unused
   *	   sss				  Source type
   */
  #define NRSTYP	  0x0f		  /* Source type mask */
  #define NRSBYT	  0x00		  /* lo byte */
  #define NRSSEG	  0x02		  /* 16-bit segment */
  #define NRSPTR	  0x03		  /* 32-bit pointer */
  #define NRSOFF	  0x05		  /* 16-bit offset */
  #define NRSPTR48	  0x0B		  /* 48-bit pointer */
  #define NRSOFF32	  0x0D		  /* 32-bit offset */

  /*
   *  Format of NR_FLAGS(x):
   *
   *  xxxxx				  Unused
   *	   a				  Additive fixup
   *	    rr				  Reference type
   */
  #define NRADD 	  0x04		  /* Additive fixup */
  #define NRRTYP	  0x03		  /* Reference type mask */
  #define NRRINT	  0x00		  /* Internal reference */
  #define NRRORD	  0x01		  /* Import by ordinal */
  #define NRRNAM	  0x02		  /* Import by name */
  #define NRROSF	  0x03		  /* Operating system fixup */


  /* Resource type or name string */
  struct rsrc_string
      {
      char rs_len;	      /* number of bytes in string */
      char rs_string[ 1 ];    /* text of string */
      };
  #define RS_LEN( x )	 (x).rs_len
  #define RS_STRING( x ) (x).rs_string

  /* Resource type information block */
  struct rsrc_typeinfo
      {
      U16 rt_id;
      U16 rt_nres;
      U32 rt_proc;
      };

  #define RT_ID( x )   (x).rt_id
  #define RT_NRES( x ) (x).rt_nres
  #define RT_PROC( x ) (x).rt_proc

  /* Resource name information block */
  struct rsrc_nameinfo
      {
      /* The following two fields must be shifted left by the value of	*/
      /* the rs_align field to compute their actual value. This allows */
      /* resources to be larger than 64k, but they do not need to be	*/
      /* aligned on 512 byte boundaries, the way segments are.		 */
      U16 rn_offset;   /* file offset to resource data */
      U16 rn_length;   /* length of resource data */
      U16 rn_flags;	  /* resource flags */
      U16 rn_id;	  /* resource name id */
      U16 rn_handle;   /* If loaded, then global handle */
      U16 rn_usage;	  /* Initially zero. Number of times */
				  /* the handle for this resource has */
				  /* been given out */
      };

  #define RN_OFFSET( x ) (x).rn_offset
  #define RN_LENGTH( x ) (x).rn_length
  #define RN_FLAGS( x )  (x).rn_flags
  #define RN_ID( x )	 (x).rn_id
  #define RN_HANDLE( x ) (x).rn_handle
  #define RN_USAGE( x )  (x).rn_usage

  #define RSORDID     0x8000	  /* if high bit of ID set then integer id */
				  /* otherwise ID is offset of string from
				     the beginning of the resource table */
				  /* Ideally these are the same as the */
				  /* corresponding segment flags */
  #define RNMOVE      0x0010	  /* Moveable resource */
  #define RNPURE      0x0020	  /* Pure (read-only) resource */
  #define RNPRELOAD   0x0040	  /* Preloaded resource */
  #define RNDISCARD   0xF000	  /* Discard priority level for resource */

  /* Resource table */
  struct new_rsrc
      {
      U16 rs_align;	  /* alignment shift count for resources */
      struct rsrc_typeinfo rs_typeinfo;
      };

  #define RS_ALIGN( x ) (x).rs_align



/* begin of Caolan */


#define RT_CURSOR   	1
#define RT_BITMAP   	2
#define RT_ICON 		3
#define RT_MENU 		4
#define RT_DIALOG   	5
#define RT_STRING 		6
#define RT_FONTDIR  	7
#define RT_FONT 		8
#define RT_ACCELERATOR  9
#define RT_RCDATA 		10
#define RT_MESSAGELIST 	11
#define RT_GROUP_CURSOR 12

#define RT_GROUP_ICON   14

#define RT_VERSION		16
#define RT_DLGINCLUDE	17
#define RT_PLUGPLAY 	19
#define RT_VXD 			20
#define RT_ANICURSOR 	21

#define RT_NEWRESOURCE  0x2000
#define RT_NEWBITMAP    (RT_BITMAP|RT_NEWRESOURCE)
#define RT_NEWMENU      (RT_MENU|RT_NEWRESOURCE)
#define RT_NEWDIALOG    (RT_DIALOG|RT_NEWRESOURCE)
#define RT_ERROR        0x7fff



typedef struct _NAMEINFO 
	{
    U16 rnOffset;
    U16 rnLength;
    U16 rnFlags;
    U16 rnID;
    U16 rnHandle;
    U16 rnUsage;
	} NAMEINFO;

void wvGetNAMEINFO(NAMEINFO *n,FILE *fd);

typedef struct _TYPEINFO 
	{
    U16 rtTypeID;
    U16 rtResourceCount;
    U32 rtReserved;
    NAMEINFO *rtNameInfo;
	} TYPEINFO;

int wvGetTYPEINFO(TYPEINFO *t,FILE *fd);
void wvReleaseTYPEINFO(TYPEINFO *t);

typedef struct _ResourceTable
	{
	U16 rscAlignShift;
	TYPEINFO *rscTypes;
	U16 rscEndTypes;
	S8 **rscResourceNames;
	U8 rscEndNames;
	} ResourceTable;


void wvGetDOSHdr(DOSHdr *header,FILE *fd);
void wvGetNEHdr(NEHrd *neheader,FILE *fd);
void wvGetResourceTable(ResourceTable *r,FILE *fd);
void wvReleaseResourceTable(ResourceTable *r);

typedef struct _IMAGE_FILE_HEADER
	{
	U32 signaturebytes;
	U16 Machine;
	U16 NumberOfSections;
	U32 TimeDateStamp;
	U32 PointerToSymbolTable;
	U32 NumberOfSymbols;
	U16 SizeOfOptionalHeader;
	U16 Characteristics;
	} IMAGE_FILE_HEADER;

void wvGetIMAGE_FILE_HEADER(IMAGE_FILE_HEADER *peheader,FILE *fd);

/* Directory Entries */

/* Export Directory */
#define IMAGE_DIRECTORY_ENTRY_EXPORT         0
/* Import Directory */
#define IMAGE_DIRECTORY_ENTRY_IMPORT         1
/* Resource Directory */
#define IMAGE_DIRECTORY_ENTRY_RESOURCE       2
/* Exception Directory */
#define IMAGE_DIRECTORY_ENTRY_EXCEPTION      3
/* Security Directory */
#define IMAGE_DIRECTORY_ENTRY_SECURITY       4
/* Base Relocation Table */
#define IMAGE_DIRECTORY_ENTRY_BASERELOC      5
/* Debug Directory */
#define IMAGE_DIRECTORY_ENTRY_DEBUG          6
/* Description String */
#define IMAGE_DIRECTORY_ENTRY_COPYRIGHT      7
/* Machine Value (MIPS GP) */
#define IMAGE_DIRECTORY_ENTRY_GLOBALPTR      8
/* TLS Directory */
#define IMAGE_DIRECTORY_ENTRY_TLS            9
/* Load Configuration Directory */
#define IMAGE_DIRECTORY_ENTRY_LOAD_CONFIG    10

typedef struct _IMAGE_DATA_DIRECTORY 
	{
    U32 VirtualAddress;
	U32 Size;
	} IMAGE_DATA_DIRECTORY;

typedef struct _IMAGE_OPTIONAL_HEADER 
	{
	/*
     Standard fields.
    */
    U16  Magic;
    U8   MajorLinkerVersion;
    U8   MinorLinkerVersion;
    U32   SizeOfCode;
    U32   SizeOfInitializedData;
    U32   SizeOfUninitializedData;
    U32   AddressOfEntryPoint;
    U32   BaseOfCode;
    U32   BaseOfData;
    /*
     NT additional fields.
    */
    U32   ImageBase;
    U32   SectionAlignment;
    U32   FileAlignment;
    U16  MajorOperatingSystemVersion;
    U16  MinorOperatingSystemVersion;
    U16  MajorImageVersion;
    U16  MinorImageVersion;
    U16  MajorSubsystemVersion;
    U16  MinorSubsystemVersion;
    U32   Reserved1;
    U32   SizeOfImage;
    U32   SizeOfHeaders;
    U32   CheckSum;
    U16  Subsystem;
    U16  DllCharacteristics;
    U32   SizeOfStackReserve;
    U32   SizeOfStackCommit;
    U32   SizeOfHeapReserve;
    U32   SizeOfHeapCommit;
    U32   LoaderFlags;
    U32   NumberOfRvaAndSizes;
	IMAGE_DATA_DIRECTORY *DataDirectory;
	} IMAGE_OPTIONAL_HEADER;

void wvGetIMAGE_OPTIONAL_HEADER(IMAGE_OPTIONAL_HEADER *nt,FILE *fd);

void wvGetIMAGE_DATA_DIRECTORY(IMAGE_DATA_DIRECTORY *id,FILE *fd);

#define IMAGE_SIZEOF_SHORT_NAME 8

typedef struct _IMAGE_SECTION_HEADER 
	{
    U8 Name[IMAGE_SIZEOF_SHORT_NAME];
    union 
		{
        U32 PhysicalAddress;
        U32 VirtualSize;
    	} Misc;
    U32 VirtualAddress;
    U32 SizeOfRawData;
    U32 PointerToRawData;
    U32 PointerToRelocations;
    U32 PointerToLinenumbers;
    U16 NumberOfRelocations;
    U16 NumberOfLinenumbers;
    U32 Characteristics;
	} IMAGE_SECTION_HEADER;

void wvGetIMAGE_SECTION_HEADER(IMAGE_SECTION_HEADER *h,FILE *fd);

U32 ImageDirectoryOffset (IMAGE_FILE_HEADER *hdr,IMAGE_OPTIONAL_HEADER *poh, IMAGE_SECTION_HEADER *psh,U32 dwIMAGE_DIRECTORY);
U32 VirtualToReal (IMAGE_FILE_HEADER *hdr,U32 VAImageDir,IMAGE_SECTION_HEADER *psh);


typedef struct _IMAGE_RESOURCE_DIRECTORY 
	{
    U32 Characteristics;
    U32 TimeDateStamp;
    U16 MajorVersion;
    U16 MinorVersion;
    U16 NumberOfNamedEntries;
    U16 NumberOfIdEntries;
	} IMAGE_RESOURCE_DIRECTORY;

void wvGetIMAGE_RESOURCE_DIRECTORY(IMAGE_RESOURCE_DIRECTORY *id,FILE *fd);

typedef struct _IMAGE_RESOURCE_DIRECTORY_ENTRY 
	{
    U32 Name;
	U32 OffsetToData;
	} IMAGE_RESOURCE_DIRECTORY_ENTRY;

void wvGetIMAGE_RESOURCE_DIRECTORY_ENTRY(IMAGE_RESOURCE_DIRECTORY_ENTRY *ie,FILE *fd);

typedef struct _IMAGE_RESOURCE_DATA_ENTRY 
	{
    U32 OffsetToData;
    U32 Size;
    U32 CodePage;
    U32 Reserved;
	} IMAGE_RESOURCE_DATA_ENTRY;

void wvGetIMAGE_RESOURCE_DATA_ENTRY(IMAGE_RESOURCE_DATA_ENTRY *de,FILE *fd);

void GetResourceTypeName(U32 type, char *buffer, int cBytes);
void GetResourceNameFromId (U32 id, char *buffer, int cBytes, FILE *ne, U32 orig);


#define IMAGE_RESOURCE_DATA_IS_DIRECTORY 0x80000000L
#define IMAGE_RESOURCE_NAME_IS_STRING	0x80000000L


/* end of Caolan */
