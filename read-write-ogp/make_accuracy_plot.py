####################################################################################
#
#  Filename    : EvtGenNtuplizer.cc
#  Description : Make an accuracy plot with offsets and angles of HGCAL 
#                module components w.r.t. baseplate components
#  Author      : You-Ying Li [ you-ying.li@cern.ch ]
#
####################################################################################

#################################
# Modified by Paolo Jordano     
# pjordano@ucsb.edu             
# Mod Version 1.0
#################################

# 1.0 FOR USE IN CMU's READ_WRITE_OGP DATABASE     9/19/24

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator
import matplotlib.patches as patches
import matplotlib as mpl
import os

mpl.use('Agg')

def make_fake_plot():
    fig, ax = plt.subplots(3, 2)
    ax[-1, -1].axis('off')  # Hide the last subplot

    from io import BytesIO  
    buffer = BytesIO(); module_name = "jerry";
    #plt.savefig(f"{(module_name.split('/'))[-1]}.png", bbox_inches='tight') # uncomment here for saving the 2d plot
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    return buffer.read() 

def make_accuracy_plot(
        module_name = 'M01',
        rel_sensor_X = 0.,
        rel_sensor_Y = 0.,
        rel_pcb_X = 0.,
        rel_pcb_Y = 0.,
        rel_sensor_angle = 0.,
        rel_pcb_angle    = 0.
        ):

    #######################||Variable Info||#################################

    """
    rel_sensor_X : relative X of sensor w.r.t. baseplate [unit : mm]
    rel_sensor_Y : relative Y of sensor w.r.t. baseplate [unit : mm]
    rel_pcb_X    : relative X of pcb w.r.t. baseplate    [unit : mm]
    rel_pcb_Y    : relative Y of pcb w.r.t. baseplate    [unit : mm]
    rel_sensor_angle : relative angle of sensor w.r.t. baseplate [unit : degree]
    rel_pcb_angle    : relative angle of pcb w.r.t. baseplate    [unit : degree]
    """
    ##############################################################
    
    #  if len(data_list) == 1:
    #       module_name = data_list[0].split()[0]
    #   elif len(data_list) > 1:
    #       module_name = "Merged"

    fig, ax = plt.subplots(figsize=(6,6), layout='constrained')
    ax.set_box_aspect(1)
    ax.set_title(f'{module_name} accuracy plot', y=1.15, fontsize=20)


    #################################
    #          Offset part          #
    #################################

    ax.set_xlabel(r'$\Delta x$ [$\mu m$]',  fontsize=18)
    ax.set_ylabel(r'$\Delta y$ [$\mu m$]', fontsize=18)
    ax.xaxis.set_major_locator(MultipleLocator(100))
    ax.yaxis.set_major_locator(MultipleLocator(100))
    ax.xaxis.set_minor_locator(MultipleLocator(25))
    ax.yaxis.set_minor_locator(MultipleLocator(25))
    ax.set_xlim(-200, 300)
    ax.set_ylim(-200, 300)
    ax.vlines(-50, -50, 50, colors='b')
    ax.vlines( 50, -50, 50, colors='b')
    ax.hlines(-50, -50, 50, colors='b')
    ax.hlines( 50, -50, 50, colors='b')
    ax.text(-50, 55, r'50 $\mu m$', color='b', fontsize=12)
    ax.vlines(-100, -100, 100, colors='r')
    ax.vlines( 100, -100, 100, colors='r')
    ax.hlines(-100, -100, 100, colors='r')
    ax.hlines( 100, -100, 100, colors='r')
    ax.text(-100, 105, r'100 $\mu m$', color='r', fontsize=12)
#    ax.vlines(0, -200, 300, colors='k')
#    ax.hlines(0, -200, 300, colors='k')

    """rel_sensor_X = rel_sensor_X * 1000  #Modified here to have Manual Input
    rel_sensor_Y = rel_sensor_Y * 1000
    rel_pcb_X    = rel_pcb_X * 1000
    rel_pcb_Y    = rel_pcb_Y * 1000"""

    limit_func = lambda x: 115. if x > 100. else -115. if x < -100. else x

    m_rel_sensor_X = limit_func( rel_sensor_X )  
    m_rel_sensor_Y = limit_func( rel_sensor_Y )
    m_rel_pcb_X    = limit_func( rel_pcb_X    )
    m_rel_pcb_Y    = limit_func( rel_pcb_Y    )


    ax.plot(m_rel_sensor_X, m_rel_sensor_Y, marker='o', markerfacecolor='#ff7f0e', markeredgecolor='#ff7f0e', linestyle = 'None', label = 'Sensor w.r.t. Baseplate')
    ax.plot(m_rel_pcb_X,    m_rel_pcb_Y,    marker='o', markerfacecolor='#2ca02c', markeredgecolor='#2ca02c', linestyle = 'None', label = 'PCB w.r.t. Baseplate')

    if abs(m_rel_sensor_X) > 100. or abs(m_rel_sensor_Y) > 100.:
        ax.text(m_rel_sensor_X, m_rel_sensor_Y, f'({rel_sensor_X:.0f}, {rel_sensor_Y:.0f})', color='#ff7f0e',
                ha='right' if m_rel_sensor_X < -100. else 'left', va='top' if m_rel_sensor_Y < -100. else 'bottom')

    if abs(m_rel_pcb_X) > 100. or abs(m_rel_pcb_Y) > 100.:
        ax.text(m_rel_pcb_X, m_rel_pcb_Y, f'({rel_pcb_X:.0f}, {rel_pcb_Y:.0f})', color='#2ca02c',
                ha='right' if m_rel_sensor_X < -100. else 'left', va='top' if m_rel_sensor_Y < -100. else 'bottom')



    ax.plot(np.array([0.]), np.array([0.]), marker='o', markerfacecolor='k', markeredgecolor='k', linestyle = 'None', label = 'Baseplate')


    plt.tick_params(axis='both', which='minor', direction='in', labelsize=0, length=5, width=1, right=True, top=True)
    plt.tick_params(axis='both', which='major', direction='in', labelsize=18, length=7, width=1.5, right=True, top=True)


    # Legend is hardcore 
    legend_elements = [ Line2D([0], [0], marker='o', color='w', label='Sensor w.r.t. Baseplate', markerfacecolor='#ff7f0e'),
                        Line2D([0], [0], marker='o', color='w', label='PCB w.r.t. Baseplate',    markerfacecolor='#2ca02c'),
                        Line2D([0], [0], marker='o', color='w', label='Baseplate',               markerfacecolor='k')
                        ]

    ax.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower right', ncol=2, borderaxespad=0., handles=legend_elements)


    # Outside boundary region
    ax.fill_between([-125, 125], 100, 125, color='r', alpha=0.05, linewidth=0)
    ax.fill_between([-125, 125], -100, -125, color='r', alpha=0.05, linewidth=0)
    ax.fill_between([-125, -100], -100, 100, color='r', alpha=0.05, linewidth=0)
    ax.fill_between([125, 100], -100, 100, color='r', alpha=0.05, linewidth=0)
#    ax_sub.fill_between(-1. * node, 0, 2, color='r', alpha=0.1)

        
    rect1 = patches.Rectangle((-120, -120), 240, 240, color = 'pink');
    rect2 = patches.Rectangle((-100, -100), 200, 200, color = 'white');  
    ax.add_patch(rect1); ax.add_patch(rect2); 
    
    #################################
    #      Rotation angle part      #
    #################################
    #ax_sub = fig.add_axes([.52, .58, .42, .25], polar=True)
    ax_sub = fig.add_axes([.50, .59, .42, .25], polar=True)
    


    gauge_angle_max  = 0.04
    gauge_angle_unit = 0.02
    orig_gauge_angle_max  = 40.
    transfer_factor = orig_gauge_angle_max / gauge_angle_max
    #transfer_factor = 40. / gauge_angle_max
    orig_gauge_angle_unit = transfer_factor * gauge_angle_unit

    ax_sub.set_rmax(2)
    ax_sub.get_yaxis().set_visible(False)
    ax_sub.grid(False)

    ax_sub.set_theta_offset(np.pi/2)
    ax_sub.set_thetamin(-orig_gauge_angle_max*1.2)
    ax_sub.set_thetamax(orig_gauge_angle_max*1.2)
    ax_sub.set_rorigin(-2.5)


    tick = [ax_sub.get_rmax(),ax_sub.get_rmax()*0.97]
    for t  in np.deg2rad(np.arange(0,360,orig_gauge_angle_unit*0.5)):
        ax_sub.plot([t,t], tick, lw=0.72, color="k")

    tick = [ax_sub.get_rmax(),ax_sub.get_rmax()*0.9]
    for t  in np.deg2rad(np.arange(0,360,orig_gauge_angle_unit)):
        ax_sub.plot([t,t], tick, lw=0.72, color="k")


    degree = ['{}°'.format(deg) for deg in np.round(np.arange(gauge_angle_max, -gauge_angle_max-gauge_angle_unit, -gauge_angle_unit), decimals=2)]

    ax_sub.set_thetagrids( np.arange(orig_gauge_angle_max, -orig_gauge_angle_max-orig_gauge_angle_unit, -orig_gauge_angle_unit) )
    ax_sub.set_xticklabels( degree )

    rel_sensor_angle = rel_sensor_angle  #Modified here to have Manual Input
    rel_pcb_angle    = rel_pcb_angle

    limit_angle_func = lambda x: orig_gauge_angle_max * 1.1 if x > orig_gauge_angle_max else -orig_gauge_angle_max * 1.1 if x < -orig_gauge_angle_max else x

    orig_rel_sensor_angle = limit_angle_func(transfer_factor * rel_sensor_angle)
    orig_rel_pcb_angle    = limit_angle_func(transfer_factor * rel_pcb_angle)

    if abs(orig_rel_sensor_angle) > orig_gauge_angle_max:
        ax_sub.text( orig_rel_sensor_angle * np.pi / 180., 2, f'({rel_sensor_angle:.2f}°)', color='#ff7f0e',
                ha='left' if orig_rel_sensor_angle < -orig_gauge_angle_max else 'right', va='bottom')

    if abs(orig_rel_pcb_angle) > orig_gauge_angle_max:
        ax_sub.text( (orig_rel_pcb_angle + (15 if orig_rel_pcb_angle > 0 else -15)) * np.pi / 180., 1.0, f'({rel_pcb_angle:.2f}°)', color='#2ca02c',
                ha='left' if orig_rel_pcb_angle < -orig_gauge_angle_max else 'right', va='bottom')


    if orig_rel_sensor_angle == 0:
        acolor = 'white'
    else:
        acolor = '#ff7f0e'
    ax_sub.annotate('', xy        = (orig_rel_sensor_angle * np.pi / 180., 2),
                    xytext    = (0., -2.5),
                    arrowprops= dict(color    = acolor,
                                     arrowstyle="->"),
                )
    if orig_rel_pcb_angle == 0:
        acolor = 'white'
    else:
        acolor = '#2ca02c'

    ax_sub.annotate('', xy        = (orig_rel_pcb_angle * np.pi / 180., 1.6),
                    xytext    = (0., -2.5),
                    arrowprops= dict(color    = acolor,
                                     arrowstyle="->"),
                )

#    ax_sub.annotate('', xy        = (transfer_factor * 0. * np.pi / 180., 2),
#                    xytext    = (0., -2.5),
#                    arrowprops= dict(color    ='k',
#                                     arrowstyle="->",
#                                     ),
#                )
    ax_sub.annotate('', xy        = (transfer_factor * 0.015 * np.pi / 180., 2), #this is where the tolerances are
                    xytext    = (transfer_factor * 0.015 * np.pi / 180., 0.),
                    arrowprops= dict(color    ='b',
                                     arrowstyle="-",
                                     linestyle ="dotted"
                                     ),
                )
    ax_sub.annotate('', xy        = (transfer_factor * -0.015 * np.pi / 180., 2),
                    xytext    = (transfer_factor * -0.015 * np.pi / 180., 0.),
                    arrowprops= dict(color    ='b',
                                     arrowstyle="-",
                                     linestyle ="dotted"
                                     ),
                )
    ax_sub.annotate('', xy        = (transfer_factor * 0.04 * np.pi / 180., 2),
                    xytext    = (transfer_factor * 0.04 * np.pi / 180., 0.),
                    arrowprops= dict(color    ='r',
                                     arrowstyle="-",
                                     linestyle ="dotted"
                                     ),
                )
    ax_sub.annotate('', xy        = (transfer_factor * -0.04 * np.pi / 180., 2),
                    xytext    = (transfer_factor * -0.04 * np.pi / 180., 0.),
                    arrowprops= dict(color    ='r',
                                     arrowstyle="-",
                                     linestyle ="dotted"
             
                                     ),
                )

    # Outside boundary region
    node = np.linspace(orig_gauge_angle_max * np.pi / 180., orig_gauge_angle_max * 1.2 * np.pi / 180., 50)
    ax_sub.fill_between(node, 0, 2, color='r', alpha=0.20);
    ax_sub.fill_between(-1. * node, 0, 2, color='r', alpha=0.20);

    
    

    #print("Check home folder for Output");
    #slt = plt;
    #plt.savefig(f'{module_name}_accuracy.png')
    wdir = os.getcwd();
    plt.savefig(f'{wdir}\\accuracy_plots\\{module_name}.png')
    #plt.close();  
    print(f'accuracy plot saved to: {wdir}\\accuracy_plots\\{module_name}.png')

    from io import BytesIO  
    buffer = BytesIO()
    #plt.savefig(f"{(module_name.split('/'))[-1]}.png", bbox_inches='tight') # uncomment here for saving the 2d plot
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    return buffer.read()  


#make_accuracy_plot(
#    module_name = 'RETRY',
#    rel_sensor_X = 0.070,
##    
 #   rel_sensor_Y = -0.180,
#    rel_pcb_X = 0.160,
#    rel_pcb_Y = -0.080,
#    rel_sensor_angle = 0.0065,
#    rel_pcb_angle = 0.1312
#)



