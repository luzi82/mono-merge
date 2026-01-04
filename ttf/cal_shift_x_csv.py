#!/usr/bin/env python3

import argparse
import csv
import math


def main():
    parser = argparse.ArgumentParser(
        description='Calculate x-shift and new advance width for characters'
    )
    parser.add_argument('input_csv', help='Input CSV file from dump_char_csv.py')
    parser.add_argument('--update-width-unit', help='Override width_unit for specific glyphs (format: glyph_id0:width_unit0,glyph_id1:width_unit1)', default='')
    parser.add_argument('advance_width', type=int, help='Target advance width for half-width characters')
    parser.add_argument('output_csv', help='Output CSV file with shift_x and new_advance_width columns')
    
    args = parser.parse_args()
    
    # Parse update-width-unit parameter
    width_unit_overrides = {}
    if args.update_width_unit:
        for pair in args.update_width_unit.split(','):
            glyph_index, width_unit = pair.split(':')
            width_unit_overrides[glyph_index] = int(width_unit)
    
    # Read input CSV and process
    with open(args.input_csv, 'r', encoding='utf-8') as infile, \
         open(args.output_csv, 'w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.DictReader(infile)
        
        # Add new column to fieldnames
        fieldnames = reader.fieldnames + ['shift_x']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            old_advance_width = int(row['advance_width'])
            glyph_index = row['glyph_index']
            
            # Check if width_unit should be overridden
            if glyph_index in width_unit_overrides:
                width_unit = width_unit_overrides[glyph_index]
                row['width_unit'] = width_unit
            else:
                width_unit = int(row['width_unit'])
            
            is_empty_glyph = row['is_empty_glyph'].lower() == 'true'
            
            # Calculate new advance width based on width_unit
            new_advance_width = args.advance_width * width_unit
            
            # Calculate x-shift
            if is_empty_glyph:
                # Empty glyphs don't need shifting
                # Note: lsb, xMin, xMax are empty strings for empty glyphs
                shift_x = 0
            else:
                # Parse numeric values for non-empty glyphs
                lsb = int(row['lsb'])
                xMin = int(row['xMin'])
                xMax = int(row['xMax'])
                
                # Calculate x-shift to maintain the ratio xMin:(new_advance_width-xMax)
                # old_left_margin = xMin
                # old_right_margin = old_advance_width - xMax
                # We want: (xMin + shift_x) / (new_advance_width - xMax - shift_x) = xMin / (old_advance_width - xMax)
                # Solving for shift_x:
                # (xMin + shift_x) * (old_advance_width - xMax) = xMin * (new_advance_width - xMax - shift_x)
                # xMin * (old_advance_width - xMax) + shift_x * (old_advance_width - xMax) = xMin * new_advance_width - xMin * xMax - xMin * shift_x
                # shift_x * (old_advance_width - xMax) + xMin * shift_x = xMin * new_advance_width - xMin * xMax - xMin * (old_advance_width - xMax)
                # shift_x * (old_advance_width - xMax + xMin) = xMin * (new_advance_width - old_advance_width)
                # shift_x = xMin * (new_advance_width - old_advance_width) / (old_advance_width - xMax + xMin)
                
                old_right_margin = old_advance_width - xMax
                denominator = old_right_margin + xMin
                
                if denominator != 0:
                    shift_x = xMin * (new_advance_width - old_advance_width) / denominator
                else:
                    # Fallback to center alignment if denominator is zero
                    shift_x = (new_advance_width - old_advance_width) / 2
                
                # Round shift_x: if fractional part >= 0.5, round down; otherwise round up
                frac_part = abs(shift_x) - math.floor(abs(shift_x))
                if frac_part >= 0.5:
                    shift_x = math.floor(shift_x)
                else:
                    shift_x = math.ceil(shift_x)
                
                # Update lsb, xMin, xMax for non-empty glyphs
                row['lsb'] = lsb + shift_x
                row['xMin'] = xMin + shift_x
                row['xMax'] = xMax + shift_x
            
            # Update advance_width and add shift_x for all glyphs
            row['advance_width'] = new_advance_width
            row['shift_x'] = shift_x
            
            writer.writerow(row)


if __name__ == '__main__':
    main()
