M_VECTOR_RAM_SIZE = 0x400;
STACK_SIZE = 0x400;
HEAP_SIZE = 0x6000;
MEMORY
{
    VECTORS (rx) : ORIGIN = 0x08000000, LENGTH = 0x400
    FLASH (rx) : ORIGIN = 0x08000000 + 0x400, LENGTH = 2048k - 0x400
    CCM (rwx) : ORIGIN = 0x10000000, LENGTH = 64K
    RAM (rwx) : ORIGIN = 0x20000000, LENGTH = 192k
}
ENTRY(Reset_Handler)
SECTIONS
{
    .isr_vector :
    {
        __vector_table = .;
        KEEP(*(.isr_vector))
         . = ALIGN(4);
    } > VECTORS
    __UVISOR_FLASH_OFFSET = 0x400;
    __UVISOR_FLASH_START = ORIGIN(VECTORS) + __UVISOR_FLASH_OFFSET;
    .text __UVISOR_FLASH_START :
    {
        . = ALIGN(4);
        __uvisor_main_start = .;
        *(.uvisor.main)
        __uvisor_main_end = .;
        *(.text*)
        KEEP(*(.init))
        KEEP(*(.fini))
        *crtbegin.o(.ctors)
        *crtbegin?.o(.ctors)
        *(EXCLUDE_FILE(*crtend?.o *crtend.o) .ctors)
        *(SORT(.ctors.*))
        *(.ctors)
        *crtbegin.o(.dtors)
        *crtbegin?.o(.dtors)
        *(EXCLUDE_FILE(*crtend?.o *crtend.o) .dtors)
        *(SORT(.dtors.*))
        *(.dtors)
        *(.rodata*)
        KEEP(*(.eh_frame*))
    } > FLASH
    .ARM.extab :
    {
        *(.ARM.extab* .gnu.linkonce.armextab.*)
    } > FLASH
    __exidx_start = .;
    .ARM.exidx :
    {
        *(.ARM.exidx* .gnu.linkonce.armexidx.*)
    } > FLASH
    __exidx_end = .;
    __etext = .;
    _sidata = .;
    .interrupts_ram :
    {
        . = ALIGN(4);
        __VECTOR_RAM__ = .;
        __interrupts_ram_start__ = .;
        *(.m_interrupts_ram)
        . += M_VECTOR_RAM_SIZE;
        . = ALIGN(4);
        __interrupts_ram_end__ = .;
    } > RAM
    __UVISOR_SRAM_OFFSET = 0x0;
    __UVISOR_SRAM_START = ORIGIN(CCM) + __UVISOR_SRAM_OFFSET;
    .uvisor.bss __UVISOR_SRAM_START (NOLOAD):
    {
        . = ALIGN(32);
        __uvisor_bss_start = .;
        . = ALIGN(32);
        __uvisor_bss_main_start = .;
        KEEP(*(.keep.uvisor.bss.main))
        . = ALIGN(32);
        __uvisor_bss_main_end = .;
        . = ALIGN(32);
        __uvisor_bss_boxes_start = .;
        KEEP(*(.keep.uvisor.bss.boxes))
        . = ALIGN(32);
        __uvisor_bss_boxes_end = .;
        . = ALIGN(32);
        __uvisor_bss_end = .;
    } > CCM
    .page_heap (NOLOAD) :
    {
        . = ALIGN(32);
        __uvisor_page_start = .;
        KEEP(*(.keep.uvisor.page_heap))
        . = ALIGN((1 << LOG2CEIL(LENGTH(RAM))) / 8);
        __uvisor_page_end = .;
    } > RAM
    .data :
    {
        PROVIDE( __etext = LOADADDR(.data) );
        __data_start__ = .;
        _sdata = .;
        *(vtable)
        *(.data*)
        . = ALIGN(4);
        PROVIDE_HIDDEN (__preinit_array_start = .);
        KEEP(*(.preinit_array))
        PROVIDE_HIDDEN (__preinit_array_end = .);
        . = ALIGN(4);
        PROVIDE_HIDDEN (__init_array_start = .);
        KEEP(*(SORT(.init_array.*)))
        KEEP(*(.init_array))
        PROVIDE_HIDDEN (__init_array_end = .);
        . = ALIGN(4);
        PROVIDE_HIDDEN (__fini_array_start = .);
        KEEP(*(SORT(.fini_array.*)))
        KEEP(*(.fini_array))
        PROVIDE_HIDDEN (__fini_array_end = .);
        KEEP(*(.jcr*))
        . = ALIGN(4);
        __data_end__ = .;
        _edata = .;
    } > RAM AT > FLASH
    .uvisor.secure :
    {
        . = ALIGN(32);
        __uvisor_secure_start = .;
        . = ALIGN(32);
        __uvisor_cfgtbl_start = .;
        KEEP(*(.keep.uvisor.cfgtbl))
        . = ALIGN(32);
        __uvisor_cfgtbl_end = .;
        __uvisor_cfgtbl_ptr_start = .;
        KEEP(*(.keep.uvisor.cfgtbl_ptr_first))
        KEEP(*(.keep.uvisor.cfgtbl_ptr))
        __uvisor_cfgtbl_ptr_end = .;
        __uvisor_register_gateway_ptr_start = .;
        KEEP(*(.keep.uvisor.register_gateway_ptr))
        __uvisor_register_gateway_ptr_end = .;
        . = ALIGN(32);
        __uvisor_secure_end = .;
    } > FLASH
    .uninitialized (NOLOAD):
    {
        . = ALIGN(32);
        __uninitialized_start = .;
        *(.uninitialized)
        KEEP(*(.keep.uninitialized))
        . = ALIGN(32);
        __uninitialized_end = .;
    } > RAM
    .bss (NOLOAD):
    {
        . = ALIGN(4);
        __bss_start__ = .;
        _sbss = .;
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        __bss_end__ = .;
        _ebss = .;
    } > RAM
    .heap (NOLOAD):
    {
        __uvisor_heap_start = .;
        __end__ = .;
        end = __end__;
        . += HEAP_SIZE;
        __HeapLimit = .;
        __uvisor_heap_end = .;
    } > RAM
    __StackTop = ORIGIN(RAM) + LENGTH(RAM);
    __stack = __StackTop;
    __StackLimit = __StackTop - STACK_SIZE;
    ASSERT(__StackLimit >= __HeapLimit, "Region RAM overflowed with stack and heap")
    __uvisor_flash_start = ORIGIN(VECTORS);
    __uvisor_flash_end = ORIGIN(FLASH) + LENGTH(FLASH);
    __uvisor_sram_start = ORIGIN(CCM);
    __uvisor_sram_end = ORIGIN(CCM) + LENGTH(CCM);
    __uvisor_public_sram_start = ORIGIN(RAM);
    __uvisor_public_sram_end = ORIGIN(RAM) + LENGTH(RAM);
}
