####################################################################################
#
#  Filename    : EvtGenNtuplizer.cc
#  Description : Make an accuracy plot with offsets and angles of HGCAL 
#                module components w.r.t. baseplate components
#  Author      : You-Ying Li [ you-ying.li@cern.ch ]
#
####################################################################################
# Modified by Paolo Jordano     
# pjordano@ucsb.edu             
# Mod Version 1.0

# Version 1.0 FOR USE IN CMU's READ_WRITE_OGP DATABASE     9/19/24

import os, logging
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator
import matplotlib.patches as patches
from io import BytesIO

mpl.use('Agg')
plt.rcParams['figure.constrained_layout.use'] = True
plt.rcParams['figure.constrained_layout.h_pad'] = 0.1
plt.rcParams['figure.constrained_layout.w_pad'] = 0.1

def limit_func(x):
    """Limit function to constrain values between -115 and 115"""
    return 115. if x > 100. else -115. if x < -100. else x

def limit_angle_func(x, max_angle):
    """Limit function for angles"""
    if x > max_angle:
        return max_angle * 1.1
    elif x < -max_angle:
        return -max_angle * 1.1
    return x

def make_fake_plot():
    """Create a fake plot for testing purposes"""
    fig, ax = plt.subplots(3, 2)
    ax[-1, -1].axis('off')
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    return buffer.read()  

def make_accuracy_plot(
    module_name,
    output_dir,
    rel_sensor_X=0.,
    rel_sensor_Y=0.,
    rel_sensor_angle=0.,
    rel_pcb_X=0.,
    rel_pcb_Y=0.,
    rel_pcb_angle=0.,
    
):
    """
    Create accuracy plot for HGCAL module components.
    
    Parameters:
    -----------
    module_name : str
        Name of the module
    output_dir : str
        Output directory for the plot 
    rel_sensor_X : float
        Relative X of sensor w.r.t. baseplate (mm)
    rel_sensor_Y : float
        Relative Y of sensor w.r.t. baseplate (mm)
    rel_pcb_X : float
        Relative X of PCB w.r.t. baseplate (mm)
    rel_pcb_Y : float
        Relative Y of PCB w.r.t. baseplate (mm)
    rel_sensor_angle : float
        Relative angle of sensor w.r.t. baseplate (degrees)
    rel_pcb_angle : float
        Relative angle of PCB w.r.t. baseplate (degrees)
    """
    # Create main plot
    plt.rcParams['font.size'] = 10  # Set a minimum font size
    plt.rcParams['axes.titlesize'] = 20
    plt.rcParams['axes.labelsize'] = 18
    plt.rcParams['xtick.labelsize'] = 12
    plt.rcParams['ytick.labelsize'] = 12
    
    fig, ax = plt.subplots(figsize=(6,6), layout='constrained')
    ax.set_box_aspect(1)
    ax.set_title(f'{module_name} accuracy plot', y=1.15, fontsize=20)

    # Setup main plot axes
    ax.set_xlabel(r'$\Delta x$ [$\mu m$]', fontsize=18)
    ax.set_ylabel(r'$\Delta y$ [$\mu m$]', fontsize=18)
    ax.xaxis.set_major_locator(MultipleLocator(100))
    ax.yaxis.set_major_locator(MultipleLocator(100))
    ax.xaxis.set_minor_locator(MultipleLocator(25))
    ax.yaxis.set_minor_locator(MultipleLocator(25))
    ax.set_xlim(-200, 300)
    ax.set_ylim(-200, 300)

    # Draw reference lines
    for offset in [50, 100]:
        color = 'b' if offset == 50 else 'r'
        ax.vlines(-offset, -offset, offset, colors=color)
        ax.vlines(offset, -offset, offset, colors=color)
        ax.hlines(-offset, -offset, offset, colors=color)
        ax.hlines(offset, -offset, offset, colors=color)
        ax.text(-offset, offset+5, f'{offset} $\mu m$', color=color, fontsize=12)

    # Process and plot component positions
    m_rel_sensor_X = limit_func(rel_sensor_X)
    m_rel_sensor_Y = limit_func(rel_sensor_Y)
    m_rel_pcb_X = limit_func(rel_pcb_X)
    m_rel_pcb_Y = limit_func(rel_pcb_Y)

    # Plot components
    ax.plot(m_rel_sensor_X, m_rel_sensor_Y, marker='o', markerfacecolor='#ff7f0e', 
            markeredgecolor='#ff7f0e', linestyle='None', label='Sensor w.r.t. Baseplate')
    ax.plot(m_rel_pcb_X, m_rel_pcb_Y, marker='o', markerfacecolor='#2ca02c', 
            markeredgecolor='#2ca02c', linestyle='None', label='PCB w.r.t. Baseplate')
    ax.plot([0.], [0.], marker='o', markerfacecolor='k', markeredgecolor='k', 
            linestyle='None', label='Baseplate')

    # Add labels for out-of-range points
    for x, y, color, values in [
        (m_rel_sensor_X, m_rel_sensor_Y, '#ff7f0e', (rel_sensor_X, rel_sensor_Y)),
        (m_rel_pcb_X, m_rel_pcb_Y, '#2ca02c', (rel_pcb_X, rel_pcb_Y))
    ]:
        if abs(x) > 100. or abs(y) > 100.:
            ax.text(x, y, f'({values[0]:.0f}, {values[1]:.0f})', color=color,
                   ha='right' if x < -100. else 'left',
                   va='top' if y < -100. else 'bottom')

    # Configure tick parameters
    plt.tick_params(axis='both', which='minor', direction='in', labelsize=0, 
                   length=5, width=1, right=True, top=True)
    plt.tick_params(axis='both', which='major', direction='in', labelsize=18, 
                   length=7, width=1.5, right=True, top=True)

    # Add legend
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Sensor w.r.t. Baseplate', 
               markerfacecolor='#ff7f0e'),
        Line2D([0], [0], marker='o', color='w', label='PCB w.r.t. Baseplate', 
               markerfacecolor='#2ca02c'),
        Line2D([0], [0], marker='o', color='w', label='Baseplate', 
               markerfacecolor='k')
    ]
    ax.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower right', 
             ncol=2, borderaxespad=0., handles=legend_elements)

    # Add boundary regions and rectangles
    for region in [(-125, 125, 100, 125), (-125, 125, -100, -125),
                  (-125, -100, -100, 100), (125, 100, -100, 100)]:
        ax.fill_between(region[:2], region[2], region[3], color='r', 
                       alpha=0.05, linewidth=0)

    ax.add_patch(patches.Rectangle((-120, -120), 240, 240, color='pink'))
    ax.add_patch(patches.Rectangle((-100, -100), 200, 200, color='white'))

    # Add rotation angle subplot
    ax_sub = fig.add_axes([.50, .59, .42, .25], polar=True)
    
    # Configure rotation angle subplot
    gauge_angle_max = 0.04
    gauge_angle_unit = 0.02
    orig_gauge_angle_max = 40.
    transfer_factor = orig_gauge_angle_max / gauge_angle_max
    orig_gauge_angle_unit = transfer_factor * gauge_angle_unit

    # Setup rotation angle subplot properties
    ax_sub.set_rmax(2)
    ax_sub.get_yaxis().set_visible(False)
    ax_sub.grid(False)
    ax_sub.set_theta_offset(np.pi/2)
    ax_sub.set_thetamin(-orig_gauge_angle_max*1.2)
    ax_sub.set_thetamax(orig_gauge_angle_max*1.2)
    ax_sub.set_rorigin(-2.5)

    # Add tick marks
    for tick_size, angle_step in [(0.97, orig_gauge_angle_unit*0.5),
                                 (0.9, orig_gauge_angle_unit)]:
        tick = [ax_sub.get_rmax(), ax_sub.get_rmax()*tick_size]
        for t in np.deg2rad(np.arange(0, 360, angle_step)):
            ax_sub.plot([t,t], tick, lw=0.72, color="k")

    # Setup degree labels
    degree_range = np.arange(gauge_angle_max, -gauge_angle_max-gauge_angle_unit, 
                           -gauge_angle_unit)
    degree_labels = [f'{deg}°' for deg in np.round(degree_range, decimals=2)]
    ax_sub.set_thetagrids(np.arange(orig_gauge_angle_max, 
                                   -orig_gauge_angle_max-orig_gauge_angle_unit,
                                   -orig_gauge_angle_unit))
    ax_sub.set_xticklabels(degree_labels)

    # Process and plot angles
    orig_rel_sensor_angle = limit_angle_func(transfer_factor * rel_sensor_angle,
                                           orig_gauge_angle_max)
    orig_rel_pcb_angle = limit_angle_func(transfer_factor * rel_pcb_angle,
                                         orig_gauge_angle_max)

    # Add angle labels for out-of-range angles
    if abs(orig_rel_sensor_angle) > orig_gauge_angle_max:
        ax_sub.text(orig_rel_sensor_angle * np.pi / 180., 2,
                   f'({rel_sensor_angle:.2f}°)', color='#ff7f0e',
                   ha='left' if orig_rel_sensor_angle < -orig_gauge_angle_max else 'right',
                   va='bottom')

    if abs(orig_rel_pcb_angle) > orig_gauge_angle_max:
        offset = 15 if orig_rel_pcb_angle > 0 else -15
        ax_sub.text((orig_rel_pcb_angle + offset) * np.pi / 180., 1.0,
                   f'({rel_pcb_angle:.2f}°)', color='#2ca02c',
                   ha='left' if orig_rel_pcb_angle < -orig_gauge_angle_max else 'right',
                   va='bottom')

    # Add arrows for angles
    for angle, color, rmax in [
        (orig_rel_sensor_angle, '#ff7f0e', 2),
        (orig_rel_pcb_angle, '#2ca02c', 1.6)
    ]:
        if angle == 0:
            arrow_color = 'white'
        else:
            arrow_color = color
        ax_sub.annotate('', xy=(angle * np.pi / 180., rmax),
                       xytext=(0., -2.5),
                       arrowprops=dict(color=arrow_color, arrowstyle="->"))

    # Add tolerance lines
#)
    for angle, color in [(0.015, 'b'), (0.04, 'r')]:
        for sign in [1, -1]:
            theta = transfer_factor * sign * angle * np.pi / 180.
            ax_sub.annotate('', xy=(theta, 2), xytext=(theta, 0.),
                          arrowprops=dict(color=color, arrowstyle="-",
                                        linestyle="dotted"))

    # Add boundary regions for angles
    node = np.linspace(orig_gauge_angle_max * np.pi / 180.,
                      orig_gauge_angle_max * 1.2 * np.pi / 180., 50)
    ax_sub.fill_between(node, 0, 2, color='r', alpha=0.20)
    ax_sub.fill_between(-1. * node, 0, 2, color='r', alpha=0.20)

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'{module_name}_accuracy.png')
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    logging.info(f'Accuracy plot saved to: {output_path}')

    # Return plot as bytes
    buffer = BytesIO()
    # Modified code with DPI and size constraints

    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    return buffer.read()
