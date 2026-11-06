"""Pure timeline mapping chooses observed rows; it never invents market prices."""
import math


def observation_at(time,duration,count,hook_indices,hook_seconds=7,overview_seconds=7):
    if count<1:raise ValueError('At least one observation is required')
    if not math.isfinite(duration) or duration<=0:raise ValueError('Duration must be finite and positive')
    if not math.isfinite(time):raise ValueError('Timestamp must be finite')
    if hook_seconds<0 or overview_seconds<0:raise ValueError('Segment lengths cannot be negative')
    if any(index<0 or index>=count for index in hook_indices):raise ValueError('Hook index is outside the input observations')
    has_hook=len(hook_indices)>1 and hook_seconds>0
    lead=min(hook_seconds,duration*.3) if has_hook else 0
    overview_length=min(overview_seconds,duration*.3)
    time=min(duration,max(0,time));is_hook=has_hook and time<lead
    overview=time>=duration-overview_length
    if is_hook:
        index=int(hook_indices[min(len(hook_indices)-1,int(time/lead*len(hook_indices)))])
    else:
        index=min(count-1,max(0,int((time-lead)/max(1e-9,duration-lead-overview_length)*(count-1))))
    return index,is_hook,overview
