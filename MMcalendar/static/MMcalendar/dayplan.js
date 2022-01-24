// Going to have a dedicated js file to handle our dayplanner, as we're going to have
// some special logic to make it look a little more polished.  Shouldn't be too complicated,
// but we want to hide some rendered information on load, as well as hook up our services "form"
// to buttons within the day planner.  We should be able to browse the DOM to check whether an
// event's duration collides with reserved or unavailable time, in which case we can prompt the
// user to choose a different time.  Finally, when we use the day planner buttons, we'll pull up
// a confirm prompt which gives the user a chance to review the information they are submitting.

document.addEventListener('DOMContentLoaded', () => {

    
    //We'll do selected services first, as we'll need to use their info to populate
    //requests we'll send from our schedule service button
    let serviceDetails = document.querySelectorAll(".ServiceDetails")
    let selectedService = document.querySelector("#bookingFormSelect");
    for (let i = 0; i < serviceDetails.length; i++) {
        if (serviceDetails[i].id.indexOf(`${selectedService.value}`) != -1) {
            for (let j = 0; j < serviceDetails[i].childNodes.length; j++) {
                serviceDetails[i].childNodes[j].hidden = false
            }
        } else {
            for (let j = 0; j < serviceDetails[i].childNodes.length; j++) {
                serviceDetails[i].childNodes[j].hidden = true
            }
        }
    }

    selectedService.addEventListener('change', () => {
    for (let i = 0; i < serviceDetails.length; i++) {
        if (serviceDetails[i].id.indexOf(`${selectedService.value}`) != -1) {
            for (let j = 0; j < serviceDetails[i].childNodes.length; j++) {
                serviceDetails[i].childNodes[j].hidden = false
            }
        } else {
            for (let j = 0; j < serviceDetails[i].childNodes.length; j++) {
                serviceDetails[i].childNodes[j].hidden = true
            }
        }
    }
    })

    //Alright, what we're going to do is gather all the child nodes of our hours, then assign function
    //to the "show", "collapse" and "schedule" buttons.  
    let hours = document.querySelectorAll(".hour")
    for (let i = 0; i < hours.length; i++) {

    //For the show button, I think we should disable them for completely reserved hours, as well as add 
    //styling (color coded) to indicate open hours and non-open hours. For this we need to grab the show 
    //button, but we must also read the childNodes of the the minuteContainer to find out their status.
        let showButton = hours[i].childNodes[3]
        let minuteContainer = hours[i].childNodes[5]
        let collapseButton = minuteContainer.childNodes[9]
        let unavailableCount = 0
        let freeCount = 0

        for (let j = 0; j < minuteContainer.childNodes.length; j++) {

            //So for our purposes, we need to check the first four childNodes, which gives us the divs for
            //15 minute increments, once we retrieve those, we need to check childNodes[1] for the status string
            //of the increment.  If we have 4 matching stings, they'll be free or booked, if they do not, then 
            //we'll have to signify that the hour has been partially booked.
            if (j % 2 != 0 && j < 8) {
                let specificMinute = minuteContainer.childNodes[j]
                let minuteStatus = specificMinute.childNodes[5]
                let scheduleButton = minuteStatus.childNodes[3]
                if (specificMinute.childNodes[3].innerHTML.indexOf('Open') != -1) {
                    freeCount = freeCount + 1
                    
                    //This is also an ideal time to set the event listener for the 'schedule' button, as
                    //we should not activate reserved/unavailable schedule buttons.
                    scheduleButton.addEventListener('click', () => {
                        //Okay, but what information do we need and where do we find it?  First, we need to
                        //find out what our selected service is, which is easy enough
                        
                        let serviceName = selectedService.value
                        let serviceDuration = ''
                        let serviceDescription = ''
                        let servicePrice = ''
                        let serviceStart = specificMinute.id

                        //then, we'll want to get some of the data we associate with that service
                        for (let k = 0; k < serviceDetails.length; k++) {
                            if (serviceDetails[k].id.indexOf(`${selectedService.value}`) != -1) {
                                for (let m = 0; m < serviceDetails[k].childNodes.length; m++) {
                                    if (serviceDetails[k].childNodes[m].id == `${serviceName}Duration`) {
                                        serviceDuration = serviceDetails[k].childNodes[m].innerHTML
                                    }
                                    if (serviceDetails[k].childNodes[m].id == `${serviceName}Description`) {
                                        serviceDescription = serviceDetails[k].childNodes[m].innerHTML
                                    }
                                    if (serviceDetails[k].childNodes[m].id == `${serviceName}Price`) {
                                        servicePrice = serviceDetails[k].childNodes[m].innerHTML
                                    }
                                }
                            }
                        }
                        
                        // Not done yet, we need to convert duration into something more readable.  We receive
                        // it as "duration: # hours", where # can be a decimal

                        let formattedDuration = serviceDuration.replace('Duration:', '').replace('hours', '').trim()
                        let numericalDuration = Number(formattedDuration)
                        let hourDuration = parseInt(numericalDuration)
                        let minuteSegments = (parseFloat(numericalDuration) * 60) / 15
                        let conflicts = 0
                        let error = ''

                        //js scope insanity, we need to check the availability of minute segments ahead of what is scheduled.
                        //we appear to have some information in our scope to help us, but I fear this could get messy.

                        //i is the index of the hours container we are currently in. j is the index of the current minute
                        // container.
                        for (let m = 0; m < minuteSegments; m++) {
                            // so here we are, thisindex returns a the j value iterated
                            let thisIndex = (j + m*2) % 8
                            // Our hours are the index we start at plus the number of times we have iterated over 8.  
                                // Since django's render of html included some empty spacing strings, we have to iterate
                            // over the odd numbers 1-7 to find our minute details.
                            let hoursMod = i + parseInt((j + m*2)/8)
                            if (hoursMod < 24) {
                                if (hours[hoursMod].childNodes[5].childNodes[thisIndex].childNodes[3].innerHTML.indexOf('Open') == -1) {
                                    conflicts = conflicts + 1
                                    error = error + `--Service overlaps with event at ${hours[hoursMod].childNodes[5].childNodes[thisIndex].id}`
                                }
                            } else {
                                minutesToGo = minuteSegments - m
                                minutesOverflow = Number(document.querySelector('#overflowMinutes').innerHTML)
                                if (minutesToGo > minutesOverflow) {
                                    conflicts = conflicts + 1
                                    error = error + `--Service overlaps with future unavailability`
                                }
                            }
                        }
                        //Final safety, disallow users from scheduling events in the past. For this we need to take
                        //the start time (specificMinute.id) + date (querySelector('#todayDate')).  It's also another
                        // area where our timezone issues are again apparent.
                        let startTime = serviceStart.replace('-',':').split('_')
                        let numeralTime = startTime[0].split(':')
                        if (startTime[1] == 'pm') {
                            if (numeralTime[0] != '12') {
                                hourTime = Number(numeralTime[0]) + 12
                            } else {
                                hourTime = Number(numeralTime[0])
                            }
                        } else {
                            if (numeralTime[0] == '12') {
                                hourTime = Number(numeralTime[0]) -12
                            } else {
                                hourTime = Number(numeralTime[0])
                            }
                        }
                        let timeString = hourTime.toString() + ':' + numeralTime[1] + ':' + '00'
                        let todayDate = document.querySelector('#todayDate').innerHTML
                        let combinedDatetime = todayDate + ',' + timeString 

                        //We apparently get thisEpoch in local time for free, and nowEpoch is also
                        //based on system time
                        let thisEpoch = Date.parse(combinedDatetime)
                        let nowEpoch = Date.now()
                        
                        if (nowEpoch > thisEpoch) {
                            conflicts = conflicts + 1
                            error = error + '--Event is scheduled in the past.--'
                        }

                        //Finally, with all our sweet data secured, we pass their values into our form
                        // and then submit the form.
                        if (conflicts == 0) {

                            //I was thinking of passing some scheduling details to a div on the page, but
                            //For a confirmation, I think that a simple prompt might just be most effective
                            //For this we want to humanize our serviceStart time, then pass the name of the
                            // service, duration, price and start-time
                            
                            let humanizeServiceStart = serviceStart.replace('-',':').replace('_',' ')
                            let eventConfirm = confirm(`Schedule ${serviceName} at ${humanizeServiceStart}?`)
                            if (eventConfirm == true) { 
                                document.querySelector('#bookingFormDtstart').value = serviceStart
                                document.querySelector('#bookingFormDescription').value = serviceDescription
                                document.querySelector('#bookingFormDuration').value = minuteSegments * 15
                                document.querySelector('#bookingFormPrice').value = servicePrice
                                document.querySelector('#bookingForm').submit()
                            }
                        } else {
                            //Pass an error message back to user explaning that their appointment overlaps with reserved
                            //or unavailable time.
                            alert(`Time unavailable. ${error}`)
                        }
                    })
                } else if (specificMinute.childNodes[3].innerHTML.indexOf('Anon') != -1) {
                    unavailableCount = unavailableCount + 1
                } else if (specificMinute.childNodes[3].innerHTML.indexOf('Unavailable') != -1) {
                    unavailableCount = unavailableCount + 1
                }
            }
        }
        //With that checked, we can assign function and values to our show button
        showButton.addEventListener('click', () => {
            showButton.hidden = true
            for (let j = 0; j < minuteContainer.childNodes.length; j++) {
                if (j < 8 && j % 2 != 0) {
                    minuteContainer.childNodes[j].style = ''
                } else {
                    minuteContainer.childNodes[j].hidden = false
                }
            }
        })
        if (unavailableCount == 4) {
            showButton.disabled = true
            showButton.style = 'background-color: red'
        } else if (freeCount == 4) {
            showButton.style = 'background-color: green'
        } else {
            showButton.style = 'background-color: yellow'
        }

        //Collapse Button too.
        collapseButton.addEventListener('click', () => {
            showButton.hidden = false
            for (let j = 0; j < minuteContainer.childNodes.length; j++) {
                if (j < 8 && j % 2 != 0) {
                    minuteContainer.childNodes[j].style = 'display: none'
                } else {
                    minuteContainer.childNodes[j].hidden = true
                }
            }
        })
    }
})
